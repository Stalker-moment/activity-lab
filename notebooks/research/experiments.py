"""Controlled six-class KTH experiments. No work runs on import."""
import os
os.environ.setdefault('KERAS_BACKEND','torch')
import csv, hashlib, json, time
from pathlib import Path
import cv2
import numpy as np
import pandas as pd
import torch
import keras
from sklearn.metrics import classification_report, confusion_matrix, f1_score, balanced_accuracy_score
from tqdm.auto import tqdm

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parent
CLASSES=['boxing','handclapping','handwaving','jogging','running','walking']
FRAMES=16
SIZE=160
METHODS={'E01':('full','ann'),'E02':('full','gru'),'E03':('roi','gru')}
PREPROCESS={'version':1,'frames':16,'window_seconds':2.,'size':160,'gray':True,'resize':'letterbox','detector':'yolo11n.pt','detector_conf':.25,'detector_imgsz':320,'crop_margin':.10,'minimum_detection_coverage':.8}

def check_gpu():
    torch.set_num_threads(8)
    if not torch.cuda.is_available():raise RuntimeError('CUDA tidak tersedia di kernel ini. Gunakan HumanActivity Research GPU.')
    # Warm torchvision NMS before Ultralytics' time-limited per-batch loop.
    from torchvision.ops import nms
    nms(torch.tensor([[0.,0.,10.,10.]],device='cuda'),torch.tensor([.9],device='cuda'),.5)
    torch.cuda.synchronize()
    return {'torch':torch.__version__,'torchvision':__import__('torchvision').__version__,'ultralytics':__import__('ultralytics').__version__,'keras':keras.__version__,'gpu':torch.cuda.get_device_name(0)}

def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2),encoding='utf8')

def prepare_protocol():
    """Decode once and select the same windows for every model. No test labels used for tuning."""
    folder=HERE/'protocol';folder.mkdir(exist_ok=True)
    target=folder/'windows.csv'
    if target.exists():
        manifest=pd.read_csv(target)
        expected=json.loads((folder/'protocol.json').read_text())['manifest_sha256']
        if hashlib.sha256(target.read_bytes()).hexdigest()!=expected:raise ValueError('Manifest berubah; jangan memakai cache/model lama.')
        return manifest
    source=PROJECT/'outputs_local'/'video_manifest.csv'
    videos=pd.read_csv(source)
    rows=[];decode=[]
    for r in tqdm(videos.to_dict('records'),desc='Verifikasi video bersama'):
        cap=cv2.VideoCapture(r['path']);fps=cap.get(cv2.CAP_PROP_FPS);declared=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));count=0
        if not np.isfinite(fps) or fps<=0:raise ValueError('FPS tidak valid: '+r['path'])
        while True:
            ok,frame=cap.read()
            if not ok or frame is None:break
            count+=1
        cap.release()
        decode.append({'video_id':r['video_id'],'declared':declared,'decodable_prefix':count})
        length=round(2*fps)
        if count<length:continue
        starts=list(range(0,count-length+1,max(1,round(fps))))
        if starts[-1]!=count-length:starts.append(count-length)
        if len(starts)>3:starts=[starts[i] for i in np.linspace(0,len(starts)-1,3).round().astype(int)]
        for i,start in enumerate(starts):
            rows.append({**r,'window_id':r['video_id']+f'_w{i}','start':start,'end':start+length-1,'fps':fps})
    manifest=pd.DataFrame(rows)
    if manifest.empty or manifest.window_id.duplicated().any():raise ValueError('Manifest kosong/duplikat')
    groups={s:set(manifest[manifest.split==s].subject_id) for s in ['train','val','test']}
    assert not(groups['train']&groups['val'] or groups['train']&groups['test'] or groups['val']&groups['test'])
    for s in groups:
        assert manifest[manifest.split==s].label.nunique()==6
    manifest.to_csv(target,index=False);pd.DataFrame(decode).to_csv(folder/'decode_audit.csv',index=False)
    write_json(folder/'protocol.json',{'manifest_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'preprocessing':PREPROCESS,'source_manifest':str(source),'note':'Six-class KTH benchmark; no personal/idle data. EOF-corrupt suffixes excluded uniformly before sampling. Test benchmark previously inspected in earlier development.'})
    return manifest

def read_window(r):
    indices=np.linspace(int(r['start']),int(r['end']),FRAMES).round().astype(int)
    wanted=set(indices.tolist());selected={}
    cap=cv2.VideoCapture(str(r['path']))
    try:
        for i in range(int(r['end'])+1):
            ok,frame=cap.read()
            if not ok or frame is None:raise ValueError('Decode berubah sejak protocol dibuat: '+r['window_id'])
            if i in wanted:selected[i]=frame
    finally:cap.release()
    return [selected[int(i)] for i in indices]

def letterbox(frame):
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY);rgb=cv2.cvtColor(gray,cv2.COLOR_GRAY2RGB)
    h,w=rgb.shape[:2];ratio=min(SIZE/w,SIZE/h);nw,nh=max(1,round(w*ratio)),max(1,round(h*ratio))
    out=np.zeros((SIZE,SIZE,3),dtype='uint8');x,y=(SIZE-nw)//2,(SIZE-nh)//2
    out[y:y+nh,x:x+nw]=cv2.resize(rgb,(nw,nh),interpolation=cv2.INTER_AREA)
    return out

def make_detector(pose=False):
    from ultralytics import YOLO
    return YOLO(str(HERE.parents[1]/'backend/models/hybrid'/('yolo11n-pose.pt' if pose else 'yolo11n.pt')))

def crop_people(frames,detector):
    results=detector.predict(frames,classes=[0],conf=.25,imgsz=320,device=0,verbose=False)
    crops=[];boxes=[];valid=[]
    for frame,result in zip(frames,results):
        coords=result.boxes.xyxy.detach().cpu().numpy()
        if not len(coords):
            crops.append(frame);boxes.append(None);valid.append(False);continue
        areas=(coords[:,2]-coords[:,0])*(coords[:,3]-coords[:,1]);box=coords[areas.argmax()]
        h,w=frame.shape[:2];x1,y1,x2,y2=box;mx=(x2-x1)*.1;my=(y2-y1)*.1
        x1,y1=max(0,int(x1-mx)),max(0,int(y1-my));x2,y2=min(w,int(np.ceil(x2+mx))),min(h,int(np.ceil(y2+my)))
        if x2<=x1 or y2<=y1:crops.append(frame);boxes.append(None);valid.append(False);continue
        crops.append(frame[y1:y2,x1:x2]);boxes.append([x1,y1,x2,y2]);valid.append(True)
    # Main experiment assumes a single actor. No claim of multi-person tracking.
    return crops,np.asarray(valid),boxes

def encoder_model():
    model=keras.applications.MobileNetV2(input_shape=(SIZE,SIZE,3),include_top=False,weights='imagenet',pooling='avg')
    model.trainable=False
    return model

def encode_images(frames,encoder):
    images=np.stack([letterbox(f) for f in frames]).astype('float32')
    images=keras.applications.mobilenet_v2.preprocess_input(images)
    with torch.inference_mode():return keras.ops.convert_to_numpy(encoder(images,training=False)).astype('float32')

def extract_features(manifest,representation):
    check_gpu();encoder=encoder_model();detector=make_detector() if representation=='roi' else None
    protocol=json.loads((HERE/'protocol/protocol.json').read_text())
    config={**PREPROCESS,'representation':representation,'manifest_sha256':protocol['manifest_sha256'],'keras':keras.__version__,'torch':torch.__version__}
    if representation=='roi':config['weights_sha256']=hashlib.sha256((HERE.parents[1]/'backend/models/hybrid/yolo11n.pt').read_bytes()).hexdigest();config['ultralytics']=__import__('ultralytics').__version__
    key=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()[:16]
    cache=HERE/'features'/key;cache.mkdir(parents=True,exist_ok=True)
    write_json(cache/'config.json',config)
    features=[];coverage=[]
    for r in tqdm(manifest.to_dict('records'),desc=representation+' CNN'):
        target=cache/(r['window_id']+'.npz')
        if target.exists():
            with np.load(target,allow_pickle=False) as z:f=z['features'];cov=float(z['coverage'])
        else:
            frames=read_window(r);cov=1.
            if detector is not None:
                frames,valid,_=crop_people(frames,detector);cov=float(valid.mean())
            f=encode_images(frames,encoder)
            temporary=target.with_suffix('.tmp.npz');np.savez(temporary,features=f,coverage=cov);temporary.replace(target)
        if f.shape!=(FRAMES,1280) or not np.isfinite(f).all():raise ValueError('Cache fitur rusak: '+str(target))
        features.append(f);coverage.append(cov)
    return np.stack(features),np.asarray(coverage),config

def build_head(kind,train_x):
    L=keras.layers;inp=L.Input((FRAMES,1280));norm=L.Normalization(axis=-1);norm.adapt(train_x.reshape(-1,1280))
    z=norm(inp);z=L.Dense(128,activation='relu')(z)
    z=L.GlobalAveragePooling1D()(z) if kind=='ann' else L.GRU(64)(z)
    z=L.Dropout(.3)(z);z=L.Dense(32,activation='relu')(z);out=L.Dense(6,activation='softmax')(z)
    model=keras.Model(inp,out);model.compile(optimizer=keras.optimizers.Adam(3e-4,clipnorm=1.),loss='sparse_categorical_crossentropy',metrics=['accuracy'])
    return model

def train_experiment(experiment,manifest,X,coverage,feature_config,seed=42,epochs=40):
    check_gpu();keras.utils.set_random_seed(seed)
    representation,kind=METHODS[experiment];folder=HERE/'results'/experiment/f'seed_{seed}'
    folder.mkdir(parents=True,exist_ok=True)
    masks={s:(manifest.split.to_numpy()==s) for s in ['train','val','test']};y=manifest.label.to_numpy(dtype='int32')
    eligible=coverage>=PREPROCESS['minimum_detection_coverage']
    train=masks['train']&eligible
    if set(y[train])!=set(range(6)):raise ValueError('Kelas train tidak lengkap setelah filter coverage')
    model=build_head(kind,X[train]);best=-1.;best_loss=float('inf');history=[];stale=0
    start=time.perf_counter()
    for epoch in range(epochs):
        h=model.fit(X[train],y[train],batch_size=32,epochs=1,verbose=0).history
        vp=model.predict(X[masks['val']],batch_size=32,verbose=0);prediction=vp.argmax(axis=1)
        prediction[~eligible[masks['val']]]=-1
        score=float(f1_score(y[masks['val']],prediction,labels=range(6),average='macro',zero_division=0))
        loss=float(-np.log(np.clip(vp[np.arange(len(vp)),y[masks['val']]],1e-8,1.)).mean())
        history.append({'epoch':epoch+1,'loss':float(h['loss'][0]),'accuracy':float(h['accuracy'][0]),'val_macro_f1':score,'val_loss':loss})
        print(f'{experiment} epoch {epoch+1}: val macro F1={score:.4f}; val loss={loss:.4f}',flush=True)
        if score>best+1e-6 or (abs(score-best)<=1e-6 and loss<best_loss):
            best,best_loss,stale=score,loss,0;model.save(folder/'best.keras')
        else:stale+=1
        if stale>=7:break
    write_json(folder/'history.json',history)
    write_json(folder/'run_config.json',{'experiment':experiment,'seed':seed,'feature_config':feature_config,'best_validation_macro_f1':best,'best_validation_loss':best_loss,'train_windows':int(train.sum()),'dropped_train_windows':int((masks['train']&~eligible).sum()),'training_seconds':time.perf_counter()-start,'selection':'validation macro F1; validation loss tie-break','classes':CLASSES,'environment':check_gpu()})
    return keras.models.load_model(folder/'best.keras'),folder

def evaluate(model,folder,manifest,X,coverage):
    """Call only after configuration is frozen; no tuning from returned test metrics."""
    mask=manifest.split.to_numpy()=='test';y=manifest.label.to_numpy(dtype='int32')[mask]
    prob=model.predict(X[mask],batch_size=32,verbose=0);pred=prob.argmax(axis=1)
    valid=coverage[mask]>=PREPROCESS['minimum_detection_coverage'];pred[~valid]=-1
    report=classification_report(y,pred,labels=list(range(6)),target_names=CLASSES,output_dict=True,zero_division=0)
    metrics={'accuracy':float((pred==y).mean()),'balanced_accuracy':float(balanced_accuracy_score(y,pred)),'macro_f1':float(f1_score(y,pred,labels=range(6),average='macro',zero_division=0)),'coverage':float(valid.mean()),'classification_report':report,'test_windows':int(mask.sum()),'missing_detection_policy':'Coverage < 0.8 counted incorrect on all test windows; not silently dropped.','note':'Six-class KTH; not independent personal-camera or idle evaluation.'}
    write_json(folder/'test_metrics.json',metrics)
    results=manifest[mask].copy();results['prediction']=[CLASSES[i] if i>=0 else 'no_person' for i in pred];results['coverage']=coverage[mask];results['score']=prob.max(axis=1);results.to_csv(folder/'test_predictions.csv',index=False)
    cm=confusion_matrix(y,pred,labels=list(range(6))+[-1]);pd.DataFrame(cm,index=CLASSES+['no_person'],columns=CLASSES+['no_person']).to_csv(folder/'confusion_matrix.csv')
    return metrics

def infer_video(experiment,video_path,seed=42):
    """Offline, causal two-second window inference with original CFR output timing."""
    import imageio_ffmpeg,subprocess
    from collections import deque
    check_gpu();representation,_=METHODS[experiment]
    folder=HERE/'results'/experiment/f'seed_{seed}'
    model=keras.models.load_model(folder/'best.keras')
    encoder=encoder_model();detector=make_detector() if representation=='roi' else None
    video_path=Path(video_path)
    if not video_path.exists():raise FileNotFoundError(video_path)
    cap=cv2.VideoCapture(str(video_path));fps=cap.get(cv2.CAP_PROP_FPS);n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if not np.isfinite(fps) or fps<=0 or min(n,w,h)<=0:cap.release();raise ValueError('Metadata video tidak valid')
    temp=folder/'inference_temporary.mp4';writer=cv2.VideoWriter(str(temp),cv2.VideoWriter_fourcc(*'mp4v'),fps,(w,h))
    if not writer.isOpened():cap.release();raise RuntimeError('Writer gagal')
    buffer=deque();last_sample=-1.;last_prediction=-1.;status='Mengumpulkan data';score=None;cov=None;records=[]
    try:
        for i in tqdm(range(n),desc='Inferensi '+experiment):
            ok,frame=cap.read()
            if not ok or frame is None:raise ValueError(f'Video gagal dibaca pada frame {i}')
            t=i/fps
            if t-last_sample>=.1-1e-8:buffer.append((t,frame.copy()));last_sample=t
            while buffer and buffer[0][0]<t-2.:buffer.popleft()
            if t>=2. and t-last_prediction>=.5-1e-8:
                times=np.array([r[0] for r in buffer]);target=np.linspace(t-2,t,FRAMES);indices=np.abs(times[:,None]-target[None,:]).argmin(axis=0)
                frames=[buffer[j][1] for j in indices];cov=1.
                if detector is not None:frames,valid,_=crop_people(frames,detector);cov=float(valid.mean())
                if cov<PREPROCESS['minimum_detection_coverage']:status='Orang tidak terdeteksi cukup';score=None
                else:
                    f=encode_images(frames,encoder)
                    with torch.inference_mode():p=keras.ops.convert_to_numpy(model(f[None],training=False))[0]
                    status=CLASSES[int(p.argmax())];score=float(p.max())
                last_prediction=t
            label=status if score is None else f'{status} | skor {score:.2f}'
            cv2.putText(frame,label,(10,30),cv2.FONT_HERSHEY_SIMPLEX,max(.4,min(w/900,1.)),(0,255,255),2)
            writer.write(frame);records.append({'frame':i,'time_sec':t,'activity':status,'model_score':score,'coverage':cov})
    finally:cap.release();writer.release()
    output=folder/'hasil_video.mp4'
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-loglevel','error','-i',str(temp),'-an','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True)
    pd.DataFrame(records).to_csv(folder/'inference_predictions.csv',index=False)
    write_json(folder/'inference_summary.json',{'input':str(video_path),'experiment':experiment,'fps':fps,'frames':len(records),'audio':'removed','assumption':'constant frame rate; one actor; closed set six classes','warning':'Demonstration only unless input is independently labeled and separate from training.'})
    return output

def pilot():
    """Detection/pose quality on TRAIN/VAL only; no accuracy claim without box ground truth."""
    from PIL import Image,ImageDraw
    check_gpu();folder=HERE/'pilot';folder.mkdir(exist_ok=True)
    videos=pd.read_csv(PROJECT/'outputs_local/video_manifest.csv')
    detector,pose=make_detector(),make_detector(True);rows=[];images=[]
    for action in CLASSES:
        for scenario in range(1,5):
            part=videos[(videos.action==action)&(videos.split=='val')&videos.video_id.str.endswith(f'_d{scenario}')]
            r=part.iloc[0];cap=cv2.VideoCapture(r.path);frame=None
            for _ in range(30):
                ok,current=cap.read()
                if not ok:break
                frame=current
            cap.release()
            if frame is None:continue
            torch.cuda.synchronize();start=time.perf_counter()
            result=detector.predict(frame,classes=[0],conf=.25,imgsz=320,device=0,verbose=False)[0]
            torch.cuda.synchronize();elapsed=time.perf_counter()-start
            pr=pose.predict(frame,conf=.25,imgsz=320,device=0,verbose=False)[0]
            points=pr.keypoints.conf.detach().cpu().numpy() if pr.keypoints is not None and pr.keypoints.conf is not None else np.empty((0,17))
            rows.append({'video_id':r.video_id,'action':action,'scenario':scenario,'persons':len(result.boxes),'pose_persons':len(points),'pose_visible_fraction':float((points[0]>=.3).mean()) if len(points) else 0.,'detector_seconds_including_first_call_warmup':elapsed})
            annotated=Image.fromarray(cv2.cvtColor(result.plot(),cv2.COLOR_BGR2RGB)).resize((320,240));images.append((action+f' d{scenario}',annotated))
    canvas=Image.new('RGB',(1280,6*270),'white');draw=ImageDraw.Draw(canvas)
    for i,(title,im) in enumerate(images):x=(i%4)*320;y0=(i//4)*270;canvas.paste(im,(x,y0+25));draw.text((x+5,y0+5),title,fill='black')
    canvas.save(folder/'detector_contact_sheet.jpg');pd.DataFrame(rows).to_csv(folder/'pilot.csv',index=False)
    write_json(folder/'summary.json',{'samples':len(rows),'detection_frame_coverage':float(np.mean([r['persons']>0 for r in rows])),'mean_pose_visible_fraction':float(np.mean([r['pose_visible_fraction'] for r in rows])),'note':'24 convenience validation frames; coverage is not detection accuracy; latency includes cold start and is not a deployment benchmark.','environment':check_gpu()})
    return pd.DataFrame(rows)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--pilot',action='store_true');args=parser.parse_args()
    if args.pilot:print(pilot().to_string(index=False))

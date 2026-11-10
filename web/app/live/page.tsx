"use client";
import { useEffect, useRef, useState } from "react";
import {
  Camera,
  Square,
  Download,
  ArrowUpRight,
  Scan,
  Activity,
  Settings2,
  AlertTriangle,
  Eye,
  ShieldAlert,
  UserCheck,
} from "lucide-react";
import { SiteHeader, SiteFooter } from "../components";
type Model = "ann" | "hybrid";
type Mode = "auto" | "body" | "face" | "hand" | "objects";
type Target = {
  box: number[];
  points?: number[][];
  label?: string;
  score?: number;
  full_body?: boolean;
  gesture?: string;
  handedness?: string;
};
type Result = {
  model: Model;
  label: string;
  display_label?: string;
  score: number;
  scores: Record<string, number>;
  score_labels?: Record<string, string>;
  score_kind?: string;
  latency_ms: number;
  route?: string;
  objects?: Target[];
  poses?: Target[];
  faces?: Target[];
  hands?: Target[];
  routing?: { reason: string; stabilized: boolean };
  warning?: string;
  time?: number;
  drowsiness?: {
    active: boolean;
    alert: boolean;
    eye_closure: number;
    yawn_score: number;
    closed_duration: number;
    yawn_duration: number;
    status: string;
  };
  fall?: {
    active: boolean;
    alert: boolean;
    aspect_ratio: number;
    downward_velocity: number;
    fallen_duration: number;
    status: string;
  };
  age?: {
    active: boolean;
    detected: boolean;
    estimated_age?: number;
    age_range: string;
    bracket: string;
    confidence: number | null;
    status: string;
  };
};
const API = process.env.NEXT_PUBLIC_INFERENCE_URL || "http://127.0.0.1:8765";
const names: Record<string, string> = {
  boxing: "Boxing",
  handclapping: "Bertepuk tangan",
  handwaving: "Melambaikan tangan",
  jogging: "Jogging",
  running: "Berlari",
  walking: "Berjalan",
};
const modes: Record<Mode, string> = {
  auto: "Otomatis",
  body: "Body & action",
  face: "Wajah",
  hand: "Tangan",
  objects: "Objek",
};
const poseLinks = [
  [5, 6],
  [5, 7],
  [7, 9],
  [6, 8],
  [8, 10],
  [5, 11],
  [6, 12],
  [11, 12],
  [11, 13],
  [13, 15],
  [12, 14],
  [14, 16],
  [0, 1],
  [0, 2],
  [1, 3],
  [2, 4],
];
const handLinks = [
  [0, 1],
  [1, 2],
  [2, 3],
  [3, 4],
  [0, 5],
  [5, 6],
  [6, 7],
  [7, 8],
  [5, 9],
  [9, 10],
  [10, 11],
  [11, 12],
  [9, 13],
  [13, 14],
  [14, 15],
  [15, 16],
  [13, 17],
  [0, 17],
  [17, 18],
  [18, 19],
  [19, 20],
];
export default function Studio() {
  const [model, setModel] = useState<Model>("hybrid"),
    [mode, setMode] = useState<Mode>("auto"),
    [custom, setCustom] = useState(""),
    [actions, setActions] = useState<string[]>([]),
    [drowsinessEnabled, setDrowsinessEnabled] = useState(false),
    [fallEnabled, setFallEnabled] = useState(false),
    [ageEnabled, setAgeEnabled] = useState(false);
  const [health, setHealth] = useState<{
      gpu: string;
      models: Record<string, { state: string }>;
    } | null>(null),
    [running, setRunning] = useState(false),
    [starting, setStarting] = useState(false),
    [pending, setPending] = useState(false),
    [error, setError] = useState(""),
    [result, setResult] = useState<Result | null>(null),
    [history, setHistory] = useState<Result[]>([]),
    [overlay, setOverlay] = useState(true),
    [devices, setDevices] = useState<MediaDeviceInfo[]>([]),
    [device, setDevice] = useState(""),
    [elapsed, setElapsed] = useState(0);
  const video = useRef<HTMLVideoElement>(null),
    capture = useRef<HTMLCanvasElement>(null),
    drawing = useRef<HTMLCanvasElement>(null),
    stage = useRef<HTMLDivElement>(null),
    stream = useRef<MediaStream | null>(null),
    frames = useRef<{ image: string; t: number }[]>([]),
    active = useRef(false),
    busy = useRef(false),
    version = useRef(0),
    abort = useRef<AbortController | null>(null),
    timers = useRef<ReturnType<typeof setInterval>[]>([]),
    started = useRef(0),
    lastRoute = useRef(""),
    probeAt = useRef(0),
    session = useRef(""),
    config = useRef({
      model,
      mode,
      actions,
      drowsinessEnabled,
      fallEnabled,
      ageEnabled,
    });
  config.current = {
    model,
    mode,
    actions,
    drowsinessEnabled,
    fallEnabled,
    ageEnabled,
  };
  function reset() {
    version.current++;
    abort.current?.abort();
    frames.current = [];
    lastRoute.current = "";
    probeAt.current = 0;
    session.current = crypto.randomUUID();
    setResult(null);
    setHistory([]);
    setError("");
    setPending(false);
  }
  function stop() {
    active.current = false;
    version.current++;
    abort.current?.abort();
    timers.current.forEach(clearInterval);
    timers.current = [];
    stream.current?.getTracks().forEach((t) => t.stop());
    stream.current = null;
    if (video.current) video.current.srcObject = null;
    frames.current = [];
    setRunning(false);
    setPending(false);
  }
  useEffect(() => {
    const q = new URLSearchParams(location.search);
    if (q.get("model") === "ann") setModel("ann");
    const c = q.get("context");
    if (c && c in modes) setMode(c as Mode);
    let live = true;
    const poll = async () => {
      try {
        const r = await fetch(API + "/health", {
          signal: AbortSignal.timeout(2500),
        });
        if (live) setHealth(await r.json());
      } catch {
        if (live) setHealth(null);
      }
    };
    poll();
    const id = setInterval(poll, 3000);
    return () => {
      live = false;
      clearInterval(id);
      active.current = false;
      timers.current.forEach(clearInterval);
      stream.current?.getTracks().forEach((t) => t.stop());
      abort.current?.abort();
    };
  }, []);
  useEffect(() => {
    const draw = () => {
      const c = drawing.current,
        v = video.current,
        s = stage.current;
      if (!c || !v || !s) return;
      c.width = s.clientWidth;
      c.height = s.clientHeight;
      const ctx = c.getContext("2d");
      if (!ctx) return;
      ctx.clearRect(0, 0, c.width, c.height);
      if (
        !overlay ||
        !running ||
        !result ||
        model !== "hybrid" ||
        !v.videoWidth
      )
        return;
      const scale = Math.min(c.width / v.videoWidth, c.height / v.videoHeight),
        w = v.videoWidth * scale,
        h = v.videoHeight * scale,
        ox = (c.width - w) / 2,
        oy = (c.height - h) / 2;
      const xy = (p: number[]) => [ox + (1 - p[0]) * w, oy + p[1] * h];
      const box = (t: Target, color: string, label = "") => {
        const b = t.box;
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.strokeRect(
          ox + (1 - b[2]) * w,
          oy + b[1] * h,
          (b[2] - b[0]) * w,
          (b[3] - b[1]) * h,
        );
        if (label) {
          ctx.font = "11px sans-serif";
          const x = ox + (1 - b[2]) * w,
            y = Math.max(14, oy + b[1] * h);
          ctx.fillStyle = "#090b10";
          ctx.fillRect(x, y - 15, ctx.measureText(label).width + 10, 15);
          ctx.fillStyle = color;
          ctx.fillText(label, x + 5, y - 4);
        }
      };
      const skeleton = (t: Target, links: number[][], color: string) => {
        const ps = t.points || [];
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = 2;
        for (const [a, b] of links) {
          if (
            !ps[a] ||
            !ps[b] ||
            (ps[a][2] ?? 1) < 0.35 ||
            (ps[b][2] ?? 1) < 0.35
          )
            continue;
          const p = xy(ps[a]),
            q = xy(ps[b]);
          ctx.beginPath();
          ctx.moveTo(...(p as [number, number]));
          ctx.lineTo(...(q as [number, number]));
          ctx.stroke();
        }
        for (const p of ps) {
          if ((p[2] ?? 1) < 0.35) continue;
          const q = xy(p);
          ctx.beginPath();
          ctx.arc(q[0], q[1], 2.5, 0, Math.PI * 2);
          ctx.fill();
        }
      };
      result.objects?.forEach((t) =>
        box(t, "#73e9d3", `${t.label} ${Math.round((t.score || 0) * 100)}%`),
      );
      result.poses?.forEach((t) => skeleton(t, poseLinks, "#b39aff"));
      result.hands?.forEach((t) => {
        skeleton(t, handLinks, "#ffba79");
        box(t, "#ffba79", t.gesture === "None" ? "Hand" : t.gesture);
      });
      ctx.fillStyle = "#87d9ff";
      result.faces?.forEach((t) =>
        t.points?.forEach((p) => {
          const q = xy(p);
          ctx.fillRect(q[0], q[1], 1.5, 1.5);
        }),
      );
    };
    draw();
    const ro = new ResizeObserver(draw);
    if (stage.current) ro.observe(stage.current);
    return () => ro.disconnect();
  }, [result, overlay, running, model]);
  async function infer() {
    if (!active.current || busy.current) return;
    const list = frames.current.slice(),
      cfg = config.current;
    if (list.length === 0) return;
    const probe =
      cfg.mode === "auto" && performance.now() - probeAt.current > 2500;
    const needsBuffer =
      cfg.model === "ann" ||
      cfg.mode === "body" ||
      (cfg.mode === "auto" && (lastRoute.current === "body" || probe));
    if (probe) probeAt.current = performance.now();
    if (needsBuffer) {
      if (
        list.length < (cfg.model === "ann" ? 16 : 2) ||
        list.at(-1)!.t - list[0].t < (cfg.model === "ann" ? 1.9 : 0.1)
      )
        return;
    }
    const sendList = !needsBuffer && list.length > 0 ? [list.at(-1)!] : list;
    const token = version.current;
    busy.current = true;
    setPending(true);
    const control = new AbortController();
    abort.current = control;
    const timeout = setTimeout(() => control.abort(), 30000);
    try {
      const r = await fetch(API + "/infer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: control.signal,
        body: JSON.stringify({
          model: cfg.model,
          mode: cfg.mode,
          custom_actions: cfg.actions,
          session_id: session.current,
          frames: sendList.map((f) => f.image),
          timestamps: sendList.map((f) => f.t),
          request_id: Date.now(),
          drowsiness_enabled: cfg.drowsinessEnabled,
          fall_detection_enabled: cfg.fallEnabled,
          age_detection_enabled: cfg.ageEnabled,
        }),
      });
      const data = await r.json();
      if (!r.ok)
        throw Error(
          typeof data.detail === "string"
            ? data.detail
            : "Permintaan inferensi ditolak.",
        );
      if (token === version.current && active.current) {
        lastRoute.current = data.raw_route || data.route || "";
        setResult(data);
        setError("");
        const { objects, poses, faces, hands, ...summary } = data;
        setHistory((h) =>
          [
            { ...summary, time: (performance.now() - started.current) / 1000 },
            ...h,
          ].slice(0, 80),
        );
      }
    } catch (e) {
      if (token === version.current && active.current)
        setError(e instanceof Error ? e.message : "Inferensi gagal");
    } finally {
      clearTimeout(timeout);
      busy.current = false;
      if (token === version.current) setPending(false);
    }
  }
  async function start() {
    if (starting || running) return;
    setStarting(true);
    reset();
    try {
      if (!navigator.mediaDevices?.getUserMedia)
        throw Error("Gunakan localhost atau HTTPS untuk mengakses kamera.");
      const media = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          ...(device
            ? { deviceId: { exact: device } }
            : { facingMode: "user" }),
        },
      });
      stream.current = media;
      video.current!.srcObject = media;
      await video.current!.play();
      setDevices(
        (await navigator.mediaDevices.enumerateDevices()).filter(
          (d) => d.kind === "videoinput",
        ),
      );
      active.current = true;
      setRunning(true);
      started.current = performance.now();
      setElapsed(0);
      timers.current.push(
        setInterval(() => {
          const v = video.current,
            c = capture.current;
          if (!v || !c || v.readyState < 2) return;
          const hybrid = config.current.model === "hybrid";
          const ratio = Math.min(
            (hybrid ? 640 : 384) / v.videoWidth,
            (hybrid ? 720 : 512) / v.videoHeight,
          );
          c.width = Math.round(v.videoWidth * ratio);
          c.height = Math.round(v.videoHeight * ratio);
          c.getContext("2d")!.drawImage(v, 0, 0, c.width, c.height);
          const t = performance.now() / 1000;
          frames.current.push({ image: c.toDataURL("image/jpeg", 0.72), t });
          frames.current = frames.current
            .filter((f) => f.t >= t - 2.08)
            .slice(-36);
        }, 62.5),
        setInterval(infer, 350),
        setInterval(
          () => setElapsed((performance.now() - started.current) / 1000),
          500,
        ),
      );
    } catch (e) {
      stop();
      setError(e instanceof Error ? e.message : "Kamera tidak tersedia.");
    } finally {
      setStarting(false);
    }
  }
  function exportLog() {
    const url = URL.createObjectURL(
      new Blob(
        [
          JSON.stringify(
            {
              model,
              mode,
              actions,
              created_at: new Date().toISOString(),
              note: "Skor belum terkalibrasi; bukan ground truth.",
              history: [...history].reverse(),
            },
            null,
            2,
          ),
        ],
        { type: "application/json" },
      ),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "activity-lab-results.json";
    a.click();
    URL.revokeObjectURL(url);
  }
  const ready = health?.models[model]?.state === "ready",
    scoreList = Object.entries(result?.scores || {})
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8),
    label =
      result?.display_label || names[result?.label || ""] || result?.label;
  return (
    <>
      <SiteHeader studio />
      <main className="studio">
        <div className="studio-heading">
          <div>
            <div className="section-eyebrow">
              YOUR CAMERA. LIVE INTELLIGENCE.
            </div>
            <h1>
              Live Studio<span> / vision lab</span>
            </h1>
            <p>Uji dua pendekatan. Lihat hasilnya langsung.</p>
          </div>
          <div className="server-status">
            <i className={ready ? "ready" : ""} />
            {ready
              ? "Model siap"
              : health
                ? "Memuat model…"
                : "Backend belum terhubung"}
            <small>{health?.gpu || "Local inference server"}</small>
          </div>
        </div>
        <div className="studio-models">
          {(["hybrid", "ann"] as Model[]).map((m) => (
            <button
              key={m}
              className={model === m ? "selected" : ""}
              onClick={() => {
                setModel(m);
                reset();
              }}
            >
              <span className="model-glyph">
                {m === "hybrid" ? <Scan /> : <Activity />}
              </span>
              <div>
                <strong>
                  {m === "hybrid" ? "Hybrid Vision" : "ANN hasil training"}
                </strong>
                <p>
                  {m === "hybrid"
                    ? "YOLO + MediaPipe + X-CLIP · konteks otomatis"
                    : "MobileNetV2 + ANN · enam aktivitas KTH"}
                </p>
              </div>
              <span className="model-tag">
                {m === "hybrid" ? "PRETRAINED" : "TRAINED"}
              </span>
            </button>
          ))}
        </div>
        <div className="studio-grid">
          <section className="camera-panel">
            <div className="panel-top">
              <span>
                <i className={running ? "pulse" : ""} />
                {running ? "CAMERA LIVE" : "CAMERA PREVIEW"}
              </span>
              <span>
                {Math.floor(elapsed / 60)
                  .toString()
                  .padStart(2, "0")}
                :
                {Math.floor(elapsed % 60)
                  .toString()
                  .padStart(2, "0")}{" "}
                · {running ? "target capture 16 fps" : "OFFLINE"}
              </span>
            </div>
            <div className="camera-stage" ref={stage}>
              <video ref={video} muted playsInline />
              <canvas ref={drawing} className="landmark-overlay" />
              {!running && (
                <div className="camera-empty">
                  <div>
                    <Camera size={35} />
                  </div>
                  <h2>Kameramu, jadi ruang eksperimen.</h2>
                  <p>
                    {model === "hybrid"
                      ? "Tubuh, wajah, tangan, dan objek. Satu kamera."
                      : "Posisikan seluruh tubuh untuk enam aktivitas KTH."}
                    <br />
                    Kamera aktif setelah kamu memberikan izin.
                  </p>
                  <button
                    className="button-white"
                    disabled={!ready || starting}
                    onClick={start}
                  >
                    <Camera size={16} />
                    {starting ? "Membuka kamera…" : "Mulai kamera"}
                  </button>
                  <small>Video dikirim ke backend terkonfigurasi · tanpa audio</small>
                </div>
              )}
              {running && (
                <div className="context-chip">
                  <i />
                  {model === "ann"
                    ? "ANN · 6 aktivitas"
                    : modes[(result?.route || mode) as Mode] ||
                      "Mencari konteks"}
                  {pending && <span> · analyzing</span>}
                </div>
              )}
              {result?.drowsiness?.alert && (
                <div className="safety-alert-badge drowsiness">
                  <AlertTriangle size={14} />
                  <span>{result.drowsiness.status}</span>
                </div>
              )}
              {result?.fall?.alert && (
                <div className="safety-alert-badge fall">
                  <AlertTriangle size={14} />
                  <span>{result.fall.status}</span>
                </div>
              )}
            </div>
            <canvas ref={capture} hidden />
            <div className="camera-toolbar">
              <select
                aria-label="Perangkat kamera"
                disabled={running}
                value={device}
                onChange={(e) => setDevice(e.target.value)}
              >
                <option value="">Kamera default</option>
                {devices.map((d) => (
                  <option key={d.deviceId} value={d.deviceId}>
                    {d.label || "Kamera"}
                  </option>
                ))}
              </select>
              <label>
                <input
                  type="checkbox"
                  checked={overlay}
                  onChange={(e) => setOverlay(e.target.checked)}
                />
                Overlay
              </label>
              <button
                className={running ? "button-stop" : "button-white"}
                disabled={!ready || starting}
                onClick={running ? stop : start}
              >
                {running ? <Square size={14} /> : <Camera size={14} />}{" "}
                {running ? "Hentikan" : "Mulai"}
              </button>
            </div>
            {error && <div className="error-message">{error}</div>}
            {model === "hybrid" && (
              <div className="mode-panel">
                <div className="control-label">
                  <Settings2 size={14} />
                  KONTEKS ANALISIS
                </div>
                <div className="mode-buttons">
                  {Object.entries(modes).map(([m, n]) => (
                    <button
                      className={mode === m ? "active" : ""}
                      key={m}
                      onClick={() => {
                        setMode(m as Mode);
                        reset();
                      }}
                    >
                      {n}
                    </button>
                  ))}
                </div>
                <p>
                  {result?.routing?.reason ||
                    "Otomatis: tangan dominan → tubuh lengkap → wajah dekat → konteks lain yang tersedia."}
                </p>
                <details>
                  <summary>
                    Tambah kandidat aksi tubuh <ArrowUpRight size={13} />
                  </summary>
                  <p>
                    Deskripsi bahasa Inggris, satu per baris (maksimal 20).
                    Menambah kandidat zero-shot, bukan melatih model baru.
                  </p>
                  <textarea
                    value={custom}
                    onChange={(e) => setCustom(e.target.value)}
                    placeholder={"playing badminton\nriding a skateboard"}
                    rows={3}
                  />
                  <button
                    className="button-ghost"
                    onClick={() => {
                      setActions(
                        custom
                          .split("\n")
                          .map((s) => s.trim().slice(0, 120))
                          .filter(Boolean)
                          .slice(0, 20),
                      );
                      reset();
                    }}
                  >
                    Terapkan kandidat
                  </button>
                  <small>{actions.length} kandidat tambahan aktif</small>
                </details>
              </div>
            )}
            {model === "hybrid" && (
              <div className="safety-panel">
                <div className="control-label">
                  <ShieldAlert size={14} />
                  FITUR KESELAMATAN (OPSIONAL)
                </div>
                <div className="safety-cards">
                  <label
                    className={`safety-card ${drowsinessEnabled ? "active" : ""} ${result?.drowsiness?.alert ? "triggered" : ""}`}
                  >
                    <div className="safety-card-head">
                      <input
                        type="checkbox"
                        checked={drowsinessEnabled}
                        onChange={(e) => {
                          setDrowsinessEnabled(e.target.checked);
                          reset();
                        }}
                      />
                      <span>
                        <Eye size={13} /> Deteksi Kantuk
                      </span>
                    </div>
                    <p>
                      Mendeteksi mata terpejam lama & menguap via blendshape
                      wajah.
                    </p>
                    {drowsinessEnabled && (
                      <div className="safety-stat">
                        <i
                          className={
                            result?.drowsiness?.alert
                              ? "bad"
                              : result?.drowsiness
                                ? "ok"
                                : ""
                          }
                        />
                        <span>
                          {result?.drowsiness?.status || "Menunggu wajah…"}
                        </span>
                        <small>
                          Mata:{" "}
                          {Math.round(
                            (result?.drowsiness?.eye_closure || 0) * 100,
                          )}
                          % · Menguap:{" "}
                          {Math.round(
                            (result?.drowsiness?.yawn_score || 0) * 100,
                          )}
                          %
                        </small>
                      </div>
                    )}
                  </label>
                  <label
                    className={`safety-card ${fallEnabled ? "active" : ""} ${result?.fall?.alert ? "triggered" : ""}`}
                  >
                    <div className="safety-card-head">
                      <input
                        type="checkbox"
                        checked={fallEnabled}
                        onChange={(e) => {
                          setFallEnabled(e.target.checked);
                          reset();
                        }}
                      />
                      <span>
                        <AlertTriangle size={13} /> Deteksi Jatuh
                      </span>
                    </div>
                    <p>
                      Mendeteksi postur horizontal mendadak & penurunan tubuh.
                    </p>
                    {fallEnabled && (
                      <div className="safety-stat">
                        <i
                          className={
                            result?.fall?.alert
                              ? "bad"
                              : result?.fall
                                ? "ok"
                                : ""
                          }
                        />
                        <span>{result?.fall?.status || "Menunggu tubuh…"}</span>
                        <small>
                          Rasio: {result?.fall?.aspect_ratio || "—"} · Turun:{" "}
                          {result?.fall?.downward_velocity || 0}
                        </small>
                      </div>
                    )}
                  </label>
                  <label
                    className={`safety-card ${ageEnabled ? "active" : ""}`}
                  >
                    <div className="safety-card-head">
                      <input
                        type="checkbox"
                        checked={false}
                        disabled
                        title="Model usia terlatih belum tersedia"
                      />
                      <span>
                        <UserCheck size={13} /> Estimasi Usia · belum tersedia
                      </span>
                    </div>
                    <p>
                      Dinonaktifkan: belum ada model usia terlatih dan
                      tervalidasi. Tidak membuat angka usia dari landmark.
                    </p>
                    {ageEnabled && (
                      <div className="safety-stat">
                        <i className={result?.age?.detected ? "ok" : ""} />
                        <span>{result?.age?.status || "Menunggu wajah…"}</span>
                        <small>
                          Rentang: {result?.age?.age_range || "—"} · Yakin:{" "}
                          {Math.round((result?.age?.confidence || 0) * 100)}%
                        </small>
                      </div>
                    )}
                  </label>
                </div>
                <p className="empty-copy">
                  Indikator eksperimental; bukan sistem darurat atau penentu
                  kelayakan mengemudi.
                </p>
              </div>
            )}
            <div className="overlay-legend">
              <span>● Objek</span>
              <span>● Pose</span>
              <span>● Wajah</span>
              <span>● Tangan</span>
              <small>Preview dicerminkan · hasil bukan ground truth</small>
            </div>
          </section>
          <aside className="results-panel">
            <div className="panel-top">
              <span>INFERENCE OUTPUT</span>
              <span>{pending ? "PROCESSING" : "READY"}</span>
            </div>
            <div className="primary-result">
              <div className="section-eyebrow">
                {result
                  ? model === "ann"
                    ? "AKTIVITAS KTH"
                    : (result.route || "vision").toUpperCase()
                  : "MENUNGGU KAMERA"}
              </div>
              <h2>{label || "Apa yang terlihat?"}</h2>
              <p>
                {result
                  ? result.score_kind === "similarity"
                    ? "Kecocokan terhadap kandidat deskripsi"
                    : result.score_kind === "blendshape"
                      ? "Indikator gerakan fisik wajah"
                      : "Skor model · belum terkalibrasi"
                  : "Mulai kamera untuk melihat analisis di sini."}
              </p>
              <div className="result-metrics">
                <div>
                  <strong>
                    {result ? `${Math.round(result.score * 100)}%` : "—"}
                  </strong>
                  <span>SKOR MODEL</span>
                </div>
                <div>
                  <strong>
                    {result ? `${Math.round(result.latency_ms)} ms` : "—"}
                  </strong>
                  <span>INFERENSI SERVER</span>
                </div>
              </div>
            </div>
            <div className="score-list">
              <div className="control-label">
                {result?.score_kind === "blendshape"
                  ? "INDIKATOR MIMIK"
                  : "KANDIDAT TERATAS"}
              </div>
              {scoreList.length ? (
                scoreList.map(([key, value]) => (
                  <div className="score-row" key={key}>
                    <div>
                      <span>
                        {result?.score_labels?.[key] || names[key] || key}
                      </span>
                      <small>{(value * 100).toFixed(1)}%</small>
                    </div>
                    <div className="score-track">
                      <i
                        style={{
                          width: `${Math.max(0, Math.min(100, value * 100))}%`,
                        }}
                      />
                    </div>
                  </div>
                ))
              ) : (
                <p className="empty-copy">
                  Hasil akan muncul setelah konteks yang sesuai tersedia.
                </p>
              )}
            </div>
            {model === "hybrid" && (
              <div className="target-counts">
                {[
                  ["Objek", result?.objects?.length],
                  ["Tubuh", result?.poses?.length],
                  ["Wajah", result?.faces?.length],
                  ["Tangan", result?.hands?.length],
                ].map(([n, c]) => (
                  <div key={n}>
                    <strong>{c ?? "—"}</strong>
                    <span>{n}</span>
                  </div>
                ))}
              </div>
            )}
            <div className="result-note">
              {result?.warning ||
                "Hybrid mendukung 80 kelas objek, 7 gestur, landmark, serta kandidat aksi yang dapat diperluas. Tidak semua aktivitas atau objek dapat dikenali."}
            </div>
          </aside>
        </div>
        <section className="history-panel">
          <div className="history-heading">
            <div>
              <div className="section-eyebrow">SESSION LOG</div>
              <h2>
                Jejak pengujian<span>{history.length} hasil terakhir</span>
              </h2>
            </div>
            <button
              className="button-ghost"
              disabled={!history.length}
              onClick={exportLog}
            >
              <Download size={14} />
              Ekspor JSON
            </button>
          </div>
          {history.length ? (
            <div className="history-table">
              <table>
                <thead>
                  <tr>
                    <th>WAKTU</th>
                    <th>KONTEKS</th>
                    <th>HASIL</th>
                    <th>SKOR</th>
                    <th>LATENSI</th>
                  </tr>
                </thead>
                <tbody>
                  {history.slice(0, 12).map((h, i) => (
                    <tr key={i}>
                      <td>{h.time?.toFixed(1)} s</td>
                      <td>{h.route || "ann"}</td>
                      <td>{h.display_label || names[h.label] || h.label}</td>
                      <td>{(h.score * 100).toFixed(1)}%</td>
                      <td>{Math.round(h.latency_ms)} ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="empty-copy">
              Belum ada prediksi. Riwayat hanya tersimpan selama sesi browser
              ini.
            </p>
          )}
        </section>
      </main>
      <SiteFooter />
    </>
  );
}

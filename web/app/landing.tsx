"use client";
import Link from "next/link";
import { useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  ScanFace,
  Hand,
  PersonStanding,
  Scan,
  Check,
  Camera,
  Layers3,
  ShieldCheck,
} from "lucide-react";
import { SiteHeader, SiteFooter, VisionGraphic } from "./components";
const features = [
  {
    id: "body",
    title: "Body & action",
    label: "Tubuh lengkap",
    icon: PersonStanding,
    count: "32+ kandidat aksi",
    text: "YOLO menemukan tubuh dan keypoint. Model video pralatih membandingkan gerakan dengan deskripsi aksi—dari berjalan hingga yoga.",
    detail: "17 keypoint pose · kandidat aksi dapat ditambah",
  },
  {
    id: "face",
    title: "Face & expression",
    label: "Wajah dominan",
    icon: ScanFace,
    count: "478 landmark wajah",
    text: "Saat wajah mendekat atau tubuh terpotong, MediaPipe memetakan wajah dan indikator mimik seperti senyum, kedipan, serta bukaan mulut.",
    detail: "52 blendshape · indikator mimik, bukan pembacaan emosi",
  },
  {
    id: "hand",
    title: "Hands & gestures",
    label: "Tangan dominan",
    icon: Hand,
    count: "21 landmark / tangan",
    text: "Dekatkan tangan untuk melihat landmark jari, sisi tangan, dan tujuh gestur bawaan seperti jempol, peace, atau telapak terbuka.",
    detail:
      "7 gestur bawaan · landmark tetap tersedia saat gestur belum dikenal",
  },
  {
    id: "objects",
    title: "Objects & context",
    label: "Objek sekitar",
    icon: Scan,
    count: "80 kelas objek",
    text: "YOLO mengenali objek yang didukung di sekitar kamera. Kotak, label, dan skor tersedia bersama analisis tubuh, wajah, atau tangan.",
    detail: "Deteksi objek berjalan bersama analisis konteks",
  },
];
export default function Landing() {
  const [active, setActive] = useState(0);
  const current = features[active];
  return (
    <div className="landing">
      <SiteHeader />
      <main className="landing-main">
        <section className="landing-hero">
          <div className="hero-art" aria-hidden="true">
            <VisionGraphic mode="face" large />
            <VisionGraphic mode="body" large />
            <VisionGraphic mode="hand" large />
          </div>
          <div className="hero-glow" />
          <div className="hero-content">
            <div className="hero-pill">
              <span />
              MULTIMODAL COMPUTER VISION
            </div>
            <h1>
              Satu kamera.
              <br />
              <span>Lebih banyak yang terlihat.</span>
            </h1>
            <p>
              Dari gerakan tubuh ke mimik wajah dan gestur tangan.
              <br className="desktop-break" /> Vision pralatih yang beradaptasi
              dengan apa yang ada di kamera.
            </p>
            <div className="hero-actions">
              <Link className="button-white" href="/live">
                Coba Live Studio <ArrowUpRight size={17} />
              </Link>
              <a className="button-ghost" href="#workflow">
                Lihat cara kerja <ArrowRight size={16} />
              </a>
            </div>
            <div className="hero-bottom">
              <span>
                <Check size={13} />
                Tanpa training ulang untuk mode hybrid
              </span>
              <span>
                <ShieldCheck size={13} />
                Backend lokal atau privat
              </span>
            </div>
          </div>
          <div className="hero-caption">
            Visualisasi sistem · bukan hasil inferensi langsung
          </div>
        </section>
        <section className="tech-strip">
          <p>DIBANGUN DENGAN MODEL DAN TOOLS OPEN-SOURCE</p>
          <div>
            <strong>
              ULTRALYTICS <span>YOLO</span>
            </strong>
            <strong>
              Google <span>MediaPipe</span>
            </strong>
            <strong>
              Microsoft <span>X-CLIP</span>
            </strong>
            <strong>
              NEXT.js <span>+ ANN</span>
            </strong>
          </div>
        </section>
        <section className="capability-section" id="capabilities">
          <div className="section-intro">
            <div className="section-eyebrow">
              BUKAN HANYA SATU JENIS DETEKSI
            </div>
            <h2>
              Satu sistem.
              <br />
              <span>Empat cara melihat.</span>
            </h2>
            <p>
              Pilih konteks secara otomatis, atau kendalikan sendiri.
              <br />
              Hasil yang terlihat, batas kemampuan yang jelas.
            </p>
          </div>
          <div className="capability-tabs">
            {features.map((f, i) => (
              <button
                onClick={() => setActive(i)}
                className={active === i ? "active" : ""}
                key={f.id}
              >
                <f.icon size={18} />
                {f.title}
                <span>0{i + 1}</span>
              </button>
            ))}
          </div>
          <div className={`capability-showcase ${current.id}`}>
            <div className="capability-image">
              <div className="visual-hud">
                <span>
                  <i />
                  MODEL VISUALIZATION
                </span>
                <span>{current.label}</span>
              </div>
              <VisionGraphic mode={current.id} />
              <div className="visual-bottom">
                <span>{current.count}</span>
                <span>ILLUSTRATION</span>
              </div>
            </div>
            <div className="capability-copy">
              <div className="section-eyebrow">
                {current.label.toUpperCase()}
              </div>
              <h3>{current.title}</h3>
              <p>{current.text}</p>
              <div className="detail-line">
                <Check size={15} />
                {current.detail}
              </div>
              <Link href={`/live?context=${current.id}`}>
                Uji di kamera <ArrowUpRight size={16} />
              </Link>
            </div>
          </div>
        </section>
        <section className="workflow-section" id="workflow">
          <div>
            <div className="section-eyebrow">CONTEXT-AWARE ROUTING</div>
            <h2>
              Kamera bergerak.
              <br />
              <span>Analisis ikut beradaptasi.</span>
            </h2>
            <p>
              Tidak perlu berganti model setiap kali framing berubah. Sistem
              melihat bagian yang tersedia, menstabilkan pilihan, lalu
              menampilkan analisis yang sesuai.
            </p>
            <ol>
              <li>
                <span>01</span>
                <div>
                  <strong>Lihat bagian yang tersedia</strong>
                  <p>
                    Deteksi tubuh, wajah, tangan, dan objek pada frame terbaru.
                  </p>
                </div>
              </li>
              <li>
                <span>02</span>
                <div>
                  <strong>Pilih konteks yang relevan</strong>
                  <p>
                    Tangan yang mendominasi, tubuh lengkap, atau wajah yang
                    terlihat jelas.
                  </p>
                </div>
              </li>
              <li>
                <span>03</span>
                <div>
                  <strong>Tampilkan hasil beserta alasannya</strong>
                  <p>
                    Overlay, skor, dan indikator mode. Tidak ada target yang
                    jelas? Sistem mengatakannya.
                  </p>
                </div>
              </li>
            </ol>
          </div>
          <div className="routing-visual">
            <div className="route-input">
              <Camera size={20} />
              <span>CAMERA INPUT</span>
              <i />
            </div>
            <div className="route-vertical" />
            <div className="route-engine">
              <Layers3 size={23} />
              <div>
                <strong>Vision router</strong>
                <span>Bagian terlihat + dominasi frame</span>
              </div>
              <span className="route-auto">AUTO</span>
            </div>
            <div className="route-branches">
              {features.map((f) => (
                <div key={f.id}>
                  <f.icon size={21} />
                  <strong>{f.label}</strong>
                  <span>
                    {f.id === "body"
                      ? "YOLO Pose + X-CLIP"
                      : f.id === "objects"
                        ? "YOLO detection"
                        : "Google MediaPipe"}
                  </span>
                </div>
              ))}
            </div>
            <p>
              <span />
              Perpindahan distabilkan agar mode tidak cepat berkedip.
            </p>
          </div>
        </section>
        <section className="models-section" id="models">
          <div className="section-intro">
            <div className="section-eyebrow">
              DUA PENDEKATAN. SATU TEMPAT PENGUJIAN.
            </div>
            <h2>
              Dilatih sendiri.
              <br />
              <span>Atau langsung pralatih.</span>
            </h2>
          </div>
          <div className="model-comparison">
            <article>
              <div className="comparison-top">
                <Layers3 size={23} />
                <span>PROJECT 01</span>
              </div>
              <h3>ANN hasil training</h3>
              <p>
                Baseline proyek untuk enam aktivitas KTH. Pipeline, kelas, dan
                bobot dipertahankan.
              </p>
              <ul>
                <li>
                  <Check />
                  MobileNetV2 + classifier ANN
                </li>
                <li>
                  <Check />
                  Enam kelas aktivitas
                </li>
                <li>
                  <Check />
                  Classifier dilatih pada dataset proyek
                </li>
                <li>
                  <Check />
                  Skor dan latensi inferensi
                </li>
              </ul>
              <Link href="/live?model=ann">
                Uji model ANN <ArrowUpRight size={16} />
              </Link>
            </article>
            <article className="featured">
              <div className="comparison-top">
                <Scan size={24} />
                <span>PROJECT 02 · PRETRAINED</span>
              </div>
              <h3>Hybrid Vision</h3>
              <p>
                YOLO, MediaPipe, dan X-CLIP bekerja bersama. Lebih banyak tugas,
                tanpa melatih ulang model.
              </p>
              <ul>
                <li>
                  <Check />
                  Objek + pose + wajah + tangan
                </li>
                <li>
                  <Check />
                  Pemilihan konteks otomatis
                </li>
                <li>
                  <Check />
                  Kandidat aksi lewat deskripsi tambahan
                </li>
                <li>
                  <Check />
                  Landmark dan kotak deteksi langsung
                </li>
              </ul>
              <Link href="/live?model=hybrid">
                Jelajahi Hybrid Vision <ArrowUpRight size={16} />
              </Link>
            </article>
          </div>
          <div className="honest-note">
            <ShieldCheck size={17} />
            <p>
              Lebih banyak kemampuan bukan berarti mengenali semuanya. YOLO
              mendukung kelas objek tertentu, MediaPipe punya gestur dan
              blendshape bawaan, dan pengenalan aksi bergantung pada kandidat
              serta kualitas video. Mimik bukan diagnosis emosi.
            </p>
          </div>
        </section>
        <section className="landing-cta">
          <div className="section-eyebrow">YOUR CAMERA. YOUR EXPERIMENT.</div>
          <h2>
            Lihat apa yang
            <br />
            bisa dibaca kameramu.
          </h2>
          <p>
            Kamera browser, backend pilihanmu.
            <br />
            Gunakan server lokal atau host inference privat.
          </p>
          <Link className="button-white" href="/live">
            Buka Live Studio <ArrowUpRight size={17} />
          </Link>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}

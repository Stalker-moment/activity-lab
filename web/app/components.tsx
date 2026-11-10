"use client";
import Link from "next/link";
import { useState } from "react";
import { Activity, ArrowUpRight, Menu, X } from "lucide-react";
export function SiteHeader({ studio = false }: { studio?: boolean }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <div className="announcement">
        <span>YOLO × Google MediaPipe</span>
        <span className="announcement-detail">
          Satu kamera. Analisis yang mengikuti konteks.
        </span>
        <Link href="/live">
          Coba langsung <ArrowUpRight size={13} />
        </Link>
      </div>
      <header className="site-header">
        <Link href="/" className="site-brand">
          <span className="site-brand-symbol">
            <Activity size={23} />
          </span>
          activity<span>lab</span>
          <i>VISION</i>
        </Link>
        <nav className={open ? "nav-open" : ""}>
          <Link href="/#capabilities" onClick={() => setOpen(false)}>
            Kemampuan
          </Link>
          <Link href="/#workflow" onClick={() => setOpen(false)}>
            Cara kerja
          </Link>
          <Link href="/#models" onClick={() => setOpen(false)}>
            Model
          </Link>
          <Link
            href="/live"
            className={studio ? "nav-active" : ""}
            onClick={() => setOpen(false)}
          >
            Live Studio
          </Link>
        </nav>
        <Link className="nav-cta" href={studio ? "/" : "/live"}>
          {studio ? "Beranda" : "Buka Live Studio"}
          <ArrowUpRight size={15} />
        </Link>
        <button
          className="mobile-menu"
          aria-label={open ? "Tutup menu" : "Buka menu"}
          onClick={() => setOpen(!open)}
        >
          {open ? <X size={21} /> : <Menu size={21} />}
        </button>
      </header>
    </>
  );
}
export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div>
        <Link href="/" className="site-brand">
          <Activity size={20} />
          activity<span>lab</span>
        </Link>
        <p>
          Computer vision untuk eksplorasi, pengujian,
          <br />
          dan pembelajaran yang bisa dilihat langsung.
        </p>
      </div>
      <div>
        <span>JELAJAHI</span>
        <Link href="/live">Live Studio</Link>
        <Link href="/#models">Model & batasan</Link>
      </div>
      <div>
        <span>TEKNOLOGI</span>
        <a
          href="https://docs.ultralytics.com/models/yolo11/"
          target="_blank"
          rel="noreferrer"
        >
          Ultralytics YOLO ↗
        </a>
        <a
          href="https://ai.google.dev/edge/mediapipe/solutions/vision"
          target="_blank"
          rel="noreferrer"
        >
          Google MediaPipe ↗
        </a>
        <a
          href="https://huggingface.co/microsoft/xclip-base-patch16-zero-shot"
          target="_blank"
          rel="noreferrer"
        >
          Microsoft X-CLIP ↗
        </a>
      </div>
      <div className="footer-bottom">
        <span>Activity Lab · Proyek Pengantar Teknologi Informasi</span>
        <span>Tidak berafiliasi dengan penyedia model.</span>
      </div>
    </footer>
  );
}
export function VisionGraphic({
  mode = "body",
  large = false,
}: {
  mode?: string;
  large?: boolean;
}) {
  const body = [
    [160, 55],
    [144, 52],
    [176, 52],
    [126, 58],
    [194, 58],
    [120, 108],
    [200, 108],
    [99, 162],
    [220, 156],
    [68, 207],
    [249, 200],
    [135, 210],
    [185, 210],
    [119, 283],
    [205, 276],
    [106, 354],
    [223, 351],
  ];
  const bodyLinks = [
    [0, 1],
    [0, 2],
    [1, 3],
    [2, 4],
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
  ];
  const hand = [
    [151, 340],
    [107, 291],
    [78, 252],
    [61, 219],
    [46, 197],
    [111, 230],
    [99, 172],
    [94, 122],
    [89, 80],
    [151, 219],
    [153, 149],
    [154, 91],
    [155, 45],
    [190, 229],
    [206, 166],
    [214, 114],
    [220, 74],
    [224, 249],
    [254, 208],
    [274, 175],
    [288, 146],
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
  return (
    <svg
      className={`vision-graphic ${large ? "large" : ""}`}
      viewBox="0 0 320 400"
      role="img"
      aria-label={`Ilustrasi analisis ${mode}, bukan inferensi langsung`}
    >
      <defs>
        <pattern
          id={`grid-${mode}`}
          width="20"
          height="20"
          patternUnits="userSpaceOnUse"
        >
          <path
            d="M20 0H0V20"
            fill="none"
            stroke="currentColor"
            strokeOpacity=".06"
          />
        </pattern>
      </defs>
      <rect width="320" height="400" fill={`url(#grid-${mode})`} />
      {mode === "body" ? (
        <>
          <path
            d="M160 28c-29 0-39 19-39 40s15 35 30 36l-31 8-21 50-31 45 15 8 32-40 15-32 4 67-20 75-13 73 20 2 21-71 19-48 22 47 25 72 22-6-19-77-21-69 5-65 17 25 34 38 14-12-29-45-25-47-30-8c19-4 25-18 25-36 0-22-12-40-37-40Z"
            fill="currentColor"
            fillOpacity=".04"
            stroke="currentColor"
            strokeOpacity=".15"
          />
          {bodyLinks.map(([a, b], i) => (
            <line
              key={i}
              x1={body[a][0]}
              y1={body[a][1]}
              x2={body[b][0]}
              y2={body[b][1]}
              stroke="currentColor"
              strokeWidth="2"
            />
          ))}
          {body.map(([x, y], i) => (
            <circle key={i} cx={x} cy={y} r="4" fill="currentColor" />
          ))}
          <rect
            x="44"
            y="18"
            width="227"
            height="360"
            rx="3"
            fill="none"
            stroke="currentColor"
            strokeOpacity=".5"
            strokeDasharray="8 5"
          />
        </>
      ) : mode === "hand" ? (
        <>
          {handLinks.map(([a, b], i) => (
            <line
              key={i}
              x1={hand[a][0]}
              y1={hand[a][1]}
              x2={hand[b][0]}
              y2={hand[b][1]}
              stroke="currentColor"
              strokeWidth="2"
            />
          ))}
          {hand.map(([x, y], i) => (
            <circle key={i} cx={x} cy={y} r="4" fill="currentColor" />
          ))}
          <path
            d="M46 197L89 80L155 45L220 74L288 146L224 249L151 340L107 291Z"
            fill="currentColor"
            fillOpacity=".025"
            stroke="currentColor"
            strokeOpacity=".15"
          />
        </>
      ) : mode === "face" ? (
        <>
          <ellipse
            cx="160"
            cy="196"
            rx="105"
            ry="148"
            fill="currentColor"
            fillOpacity=".025"
            stroke="currentColor"
            strokeOpacity=".5"
          />
          {Array.from({ length: 9 }, (_, r) =>
            Array.from({ length: 11 }, (_, c) => {
              const x = 70 + c * 18,
                y = 80 + r * 28;
              return ((x - 160) / 105) ** 2 + ((y - 196) / 148) ** 2 < 0.9 ? (
                <g key={`${r}-${c}`}>
                  <circle cx={x} cy={y} r="1.8" fill="currentColor" />
                  <path
                    d={`M${x} ${y}l18 0m-18 0l9 28m-9-28l-9 28`}
                    stroke="currentColor"
                    strokeOpacity=".22"
                    fill="none"
                  />
                </g>
              ) : null;
            }),
          )}
          <path
            d="M95 164q25-21 45 0m40 0q25-21 45 0m-65-5-12 73 25 0m-49 39q36 22 72 0"
            stroke="currentColor"
            strokeWidth="2"
            fill="none"
          />
        </>
      ) : (
        <>
          <rect
            x="38"
            y="66"
            width="124"
            height="220"
            rx="6"
            fill="currentColor"
            fillOpacity=".04"
            stroke="currentColor"
          />
          <rect
            x="175"
            y="148"
            width="99"
            height="183"
            rx="6"
            fill="currentColor"
            fillOpacity=".04"
            stroke="currentColor"
          />
          <path
            d="M87 117h30m-40 25h50m71 52h55m-55 28h55"
            stroke="currentColor"
            strokeOpacity=".4"
          />
          <circle
            cx="100"
            cy="219"
            r="30"
            fill="none"
            stroke="currentColor"
            strokeOpacity=".4"
          />
        </>
      )}
      <path
        className="scan-line"
        d="M15 0H305"
        stroke="currentColor"
        strokeOpacity=".5"
      />
    </svg>
  );
}

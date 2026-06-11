import { clsx } from "clsx";

export type CatState =
  | "idle"
  | "watching"
  | "reading"
  | "sorting"
  | "drafting"
  | "waiting_approval"
  | "executing"
  | "done"
  | "error";

interface CatIllustrationProps {
  state: CatState;
  size?: 24 | 64 | 160;
  className?: string;
}

export const CAT_STATE_TEXT: Record<CatState, string> = {
  idle: "쉬고 있어요.",
  watching: "주변을 살펴보고 있어요.",
  reading: "내용을 읽고 있어요.",
  sorting: "항목을 분류하고 있어요.",
  drafting: "초안을 작성하고 있어요.",
  waiting_approval: "확인을 기다리고 있어요.",
  executing: "처리하고 있어요.",
  done: "작업을 마쳤어요.",
  error: "도움이 필요해요.",
};

/* SVG path data per state — black-and-white line art, 1.5px uniform stroke */
function CatSVG({ state, size }: { state: CatState; size: number }) {
  const s = size;
  const strokeW = size <= 24 ? 1.5 : 2;

  const base = {
    stroke: "#0A0A0A",
    strokeWidth: strokeW,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    fill: "none",
  };

  // Shared body path scaled to viewBox 0 0 100 100
  const bodies: Record<CatState, JSX.Element> = {
    idle: (
      // Curled-up cat, eyes closed
      <>
        <ellipse cx="50" cy="62" rx="32" ry="22" {...base} />
        <path d="M30 48 Q25 28 32 24 L38 30" {...base} />
        <path d="M70 48 Q75 28 68 24 L62 30" {...base} />
        <ellipse cx="50" cy="48" rx="18" ry="14" {...base} />
        <path d="M44 50 Q50 54 56 50" {...base} />
        <path d="M43 46 Q43 48 44 46" {...base} />
        <path d="M57 46 Q57 48 56 46" {...base} />
        {/* tail curled */}
        <path
          className="cat-tail"
          d="M78 66 Q90 60 88 74 Q86 80 78 78"
          {...base}
          style={{ transformOrigin: "78px 66px" }}
        />
      </>
    ),
    watching: (
      // Cat looking forward, ears up
      <>
        <ellipse cx="50" cy="60" rx="26" ry="20" {...base} />
        <path d="M30 50 Q26 28 34 22 L40 34" {...base} />
        <path d="M70 50 Q74 28 66 22 L60 34" {...base} />
        <ellipse cx="50" cy="44" rx="20" ry="16" {...base} />
        <circle className="cat-eyes" cx="43" cy="42" r="3.5" {...base} />
        <circle className="cat-eyes" cx="57" cy="42" r="3.5" {...base} />
        <circle cx="43" cy="42" r="1.5" fill="#0A0A0A" />
        <circle cx="57" cy="42" r="1.5" fill="#0A0A0A" />
        <path d="M46 48 Q50 51 54 48" {...base} />
        <path
          className="cat-tail"
          d="M74 68 Q84 56 80 74"
          {...base}
          style={{ transformOrigin: "74px 68px" }}
        />
      </>
    ),
    reading: (
      // Cat looking down at a pile of papers
      <>
        <rect x="22" y="68" width="56" height="6" rx="2" {...base} />
        <rect x="26" y="62" width="48" height="6" rx="2" {...base} />
        <rect x="30" y="56" width="40" height="6" rx="2" {...base} />
        <ellipse cx="50" cy="48" rx="20" ry="14" {...base} />
        <path d="M32 44 Q28 26 36 20 L41 32" {...base} />
        <path d="M68 44 Q72 26 64 20 L59 32" {...base} />
        <path
          className="cat-head"
          d="M44 46 Q44 48 45 46M55 46 Q55 48 56 46"
          {...base}
          style={{ transformOrigin: "50px 46px" }}
        />
        <path d="M46 50 Q50 53 54 50" {...base} />
      </>
    ),
    sorting: (
      // Cat with paws sorting items
      <>
        <rect x="18" y="72" width="20" height="12" rx="3" {...base} />
        <rect x="44" y="68" width="20" height="16" rx="3" {...base} />
        <rect x="68" y="74" width="16" height="10" rx="3" {...base} />
        <path d="M28 72 Q28 60 38 56" {...base} />
        <path d="M54 68 Q60 56 62 56" {...base} />
        <ellipse cx="50" cy="46" rx="20" ry="16" {...base} />
        <path d="M32 42 Q28 24 36 18 L42 30" {...base} />
        <path d="M68 42 Q72 24 64 18 L58 30" {...base} />
        <circle cx="43" cy="42" r="2.5" fill="#0A0A0A" />
        <circle cx="57" cy="42" r="2.5" fill="#0A0A0A" />
        <path d="M46 50 Q50 53 54 50" {...base} />
      </>
    ),
    drafting: (
      // Cat holding a pencil, writing
      <>
        <rect x="28" y="64" width="44" height="22" rx="2" {...base} />
        <path d="M34 70 H66M34 76 H58" {...base} strokeWidth={1.5} />
        <line x1="64" y1="58" x2="54" y2="74" {...base} />
        <path d="M54 74 L52 78 L57 74" {...base} fill="#0A0A0A" />
        <ellipse cx="46" cy="46" rx="20" ry="16" {...base} />
        <path d="M28 42 Q24 24 32 18 L38 30" {...base} />
        <path d="M64 42 Q68 24 60 18 L55 30" {...base} />
        <circle cx="40" cy="42" r="2.5" fill="#0A0A0A" />
        <circle cx="52" cy="42" r="2.5" fill="#0A0A0A" />
        <path d="M42 50 Q46 53 50 50" {...base} />
      </>
    ),
    waiting_approval: (
      // Cat with item in mouth, looking at viewer
      <>
        <ellipse cx="50" cy="62" rx="24" ry="18" {...base} />
        <path d="M32 56 Q28 34 36 26 L42 38" {...base} />
        <path d="M68 56 Q72 34 64 26 L58 38" {...base} />
        <ellipse cx="50" cy="48" rx="18" ry="14" {...base} />
        <circle cx="43" cy="44" r="3" fill="#0A0A0A" />
        <circle cx="57" cy="44" r="3" fill="#0A0A0A" />
        {/* item in mouth */}
        <rect
          className="cat-item"
          x="40"
          y="54"
          width="20"
          height="10"
          rx="2"
          {...base}
          style={{ transformOrigin: "50px 59px" }}
        />
      </>
    ),
    executing: (
      // Fast-moving cat with motion lines
      <>
        <path d="M10 56 H24M10 62 H20M10 68 H16" {...base} strokeWidth={1.5} opacity={0.4} />
        <ellipse
          className="cat-body"
          cx="56"
          cy="60"
          rx="26"
          ry="18"
          {...base}
          style={{ transformOrigin: "56px 60px" }}
        />
        <path d="M38 52 Q34 32 42 26 L47 38" {...base} />
        <path d="M74 52 Q78 32 70 26 L65 38" {...base} />
        <ellipse cx="56" cy="46" rx="18" ry="14" {...base} />
        <circle cx="49" cy="43" r="2.5" fill="#0A0A0A" />
        <circle cx="63" cy="43" r="2.5" fill="#0A0A0A" />
        <path d="M52 50 Q56 53 60 50" {...base} />
        <path d="M80 58 Q90 52 88 64" {...base} />
      </>
    ),
    done: (
      // Cat with back turned, resting
      <>
        <ellipse cx="50" cy="64" rx="28" ry="20" {...base} />
        <path d="M26 58 Q22 38 30 30 L36 42" {...base} />
        <path d="M74 58 Q78 38 70 30 L64 42" {...base} />
        <ellipse cx="50" cy="44" rx="20" ry="18" {...base} />
        {/* back of head */}
        <path d="M36 38 Q50 28 64 38" {...base} />
        <path
          className="cat-tail"
          d="M76 68 Q88 60 86 76 Q84 82 76 80"
          {...base}
          style={{ transformOrigin: "76px 68px" }}
        />
      </>
    ),
    error: (
      // Cat with flat ears, looking around nervously
      <>
        <ellipse cx="50" cy="62" rx="24" ry="18" {...base} />
        {/* flat ears */}
        <path
          className="cat-ears"
          d="M30 50 Q24 36 30 30 L40 42"
          {...base}
          style={{ transformOrigin: "35px 40px" }}
        />
        <path
          className="cat-ears"
          d="M70 50 Q76 36 70 30 L60 42"
          {...base}
          style={{ transformOrigin: "65px 40px" }}
        />
        <ellipse cx="50" cy="48" rx="20" ry="16" {...base} />
        <circle cx="42" cy="45" r="3" fill="#0A0A0A" />
        <circle cx="58" cy="45" r="3" fill="#0A0A0A" />
        <path d="M45 52 Q50 50 55 52" {...base} />
        <path d="M50 24 L50 34M50 38 L50 40" {...base} strokeWidth={2} />
      </>
    ),
  };

  return (
    <svg
      viewBox="0 0 100 100"
      width={s}
      height={s}
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label={CAT_STATE_TEXT[state]}
    >
      {bodies[state]}
    </svg>
  );
}

export function CatIllustration({ state, size = 64, className }: CatIllustrationProps) {
  return (
    <div className={clsx(`cat-${state}`, className)}>
      <CatSVG state={state} size={size} />
    </div>
  );
}

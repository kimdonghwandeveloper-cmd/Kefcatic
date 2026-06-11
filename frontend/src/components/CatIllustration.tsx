/**
 * Cat state illustrations — black-and-white SVG silhouettes.
 * Design brief: no game UI, no colors beyond monochrome, no sparkles.
 * Each state maps to a unique posture.
 */

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
  size?: number;
}

export function CatIllustration({ state, size = 120 }: CatIllustrationProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label={`고양이 상태: ${state}`}
    >
      {CAT_PATHS[state]}
    </svg>
  );
}

/* ── SVG paths per state ─────────────────────────────────────────────────── */

const BASE_BODY = (
  <>
    {/* Body */}
    <ellipse cx="60" cy="72" rx="26" ry="22" stroke="#0A0A0A" strokeWidth="2" fill="white" />
    {/* Head */}
    <circle cx="60" cy="44" r="18" stroke="#0A0A0A" strokeWidth="2" fill="white" />
  </>
);

const CAT_PATHS: Record<CatState, React.ReactNode> = {
  idle: (
    <>
      {BASE_BODY}
      {/* Ears down */}
      <path d="M46 30 L42 20 L50 26" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      <path d="M74 30 L78 20 L70 26" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      {/* Closed eyes — sleeping */}
      <path d="M53 44 Q55 41 57 44" stroke="#0A0A0A" strokeWidth="1.5" fill="none" />
      <path d="M63 44 Q65 41 67 44" stroke="#0A0A0A" strokeWidth="1.5" fill="none" />
      {/* Tail curled under */}
      <path d="M86 80 Q96 88 88 94 Q80 98 76 90" stroke="#0A0A0A" strokeWidth="2" fill="none" strokeLinecap="round" />
    </>
  ),

  watching: (
    <>
      {BASE_BODY}
      {/* Ears perked up */}
      <path d="M46 30 L40 16 L52 24" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      <path d="M74 30 L80 16 L68 24" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      {/* Alert eyes — wide open */}
      <circle cx="55" cy="44" r="3.5" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <circle cx="65" cy="44" r="3.5" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <circle cx="55" cy="44" r="1.5" fill="#0A0A0A" />
      <circle cx="65" cy="44" r="1.5" fill="#0A0A0A" />
      {/* Tail raised */}
      <path d="M86 72 Q100 60 98 50" stroke="#0A0A0A" strokeWidth="2" fill="none" strokeLinecap="round" />
    </>
  ),

  reading: (
    <>
      {BASE_BODY}
      <path d="M46 30 L42 20 L50 26" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      <path d="M74 30 L78 20 L70 26" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      {/* Eyes looking down */}
      <ellipse cx="55" cy="45" rx="3" ry="2.5" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <ellipse cx="65" cy="45" rx="3" ry="2.5" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <circle cx="55" cy="46" r="1.2" fill="#0A0A0A" />
      <circle cx="65" cy="46" r="1.2" fill="#0A0A0A" />
      {/* Paper/scroll in paws */}
      <rect x="38" y="80" width="44" height="28" rx="2" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <line x1="44" y1="88" x2="76" y2="88" stroke="#0A0A0A" strokeWidth="1" />
      <line x1="44" y1="94" x2="76" y2="94" strokeWidth="1" stroke="#0A0A0A" />
      <line x1="44" y1="100" x2="64" y2="100" strokeWidth="1" stroke="#0A0A0A" />
    </>
  ),

  sorting: (
    <>
      {BASE_BODY}
      <path d="M46 30 L40 16 L52 24" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      <path d="M74 30 L80 16 L68 24" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      <ellipse cx="55" cy="44" rx="3" ry="3" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <ellipse cx="65" cy="44" rx="3" ry="3" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <circle cx="55" cy="44" r="1.2" fill="#0A0A0A" />
      <circle cx="65" cy="44" r="1.2" fill="#0A0A0A" />
      {/* Two stacks of cards being sorted */}
      <rect x="36" y="82" width="16" height="10" rx="1" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <rect x="38" y="79" width="16" height="10" rx="1" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <rect x="68" y="82" width="16" height="10" rx="1" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <rect x="66" y="79" width="16" height="10" rx="1" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
    </>
  ),

  drafting: (
    <>
      {BASE_BODY}
      <path d="M46 30 L42 20 L50 26" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      <path d="M74 30 L78 20 L70 26" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      <ellipse cx="55" cy="44" rx="3" ry="2.5" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <ellipse cx="65" cy="44" rx="3" ry="2.5" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <circle cx="55" cy="45" r="1.2" fill="#0A0A0A" />
      <circle cx="65" cy="45" r="1.2" fill="#0A0A0A" />
      {/* Pencil */}
      <rect x="62" y="78" width="6" height="24" rx="1" transform="rotate(-30 62 78)" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <path d="M55 98 L52 105 L59 103 Z" stroke="#0A0A0A" strokeWidth="1" fill="#0A0A0A" />
      {/* Paper */}
      <rect x="30" y="84" width="28" height="22" rx="2" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <line x1="35" y1="92" x2="53" y2="92" stroke="#0A0A0A" strokeWidth="1" />
      <line x1="35" y1="98" x2="48" y2="98" stroke="#0A0A0A" strokeWidth="1" />
    </>
  ),

  waiting_approval: (
    <>
      {BASE_BODY}
      <path d="M46 30 L40 16 L52 24" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      <path d="M74 30 L80 16 L68 24" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      {/* Hopeful eyes */}
      <ellipse cx="55" cy="43" rx="3.5" ry="4" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <ellipse cx="65" cy="43" rx="3.5" ry="4" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <circle cx="55" cy="44" r="1.5" fill="#0A0A0A" />
      <circle cx="65" cy="44" r="1.5" fill="#0A0A0A" />
      {/* Item held in mouth */}
      <path d="M56 56 Q60 60 64 56" stroke="#0A0A0A" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      <rect x="48" y="58" width="24" height="14" rx="2" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <line x1="52" y1="64" x2="68" y2="64" stroke="#0A0A0A" strokeWidth="1" />
    </>
  ),

  executing: (
    <>
      {BASE_BODY}
      <path d="M46 30 L40 16 L52 24" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      <path d="M74 30 L80 16 L68 24" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      <ellipse cx="55" cy="44" rx="3.5" ry="3.5" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <ellipse cx="65" cy="44" rx="3.5" ry="3.5" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <circle cx="54" cy="44" r="1.5" fill="#0A0A0A" />
      <circle cx="64" cy="44" r="1.5" fill="#0A0A0A" />
      {/* Motion lines */}
      <line x1="90" y1="55" x2="100" y2="52" stroke="#0A0A0A" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="92" y1="62" x2="103" y2="62" stroke="#0A0A0A" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="90" y1="69" x2="100" y2="72" stroke="#0A0A0A" strokeWidth="1.5" strokeLinecap="round" />
    </>
  ),

  done: (
    <>
      {BASE_BODY}
      <path d="M46 30 L42 20 L50 26" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      <path d="M74 30 L78 20 L70 26" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      {/* Satisfied closed eyes */}
      <path d="M51 44 Q55 47 59 44" stroke="#0A0A0A" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      <path d="M61 44 Q65 47 69 44" stroke="#0A0A0A" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      {/* Small smile */}
      <path d="M56 52 Q60 56 64 52" stroke="#0A0A0A" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      {/* Tail wagging */}
      <path d="M86 76 Q100 68 96 58 Q92 52 86 56" stroke="#0A0A0A" strokeWidth="2" fill="none" strokeLinecap="round" />
    </>
  ),

  error: (
    <>
      {BASE_BODY}
      <path d="M46 30 L42 20 L50 26" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      <path d="M74 30 L78 20 L70 26" stroke="#0A0A0A" strokeWidth="2" fill="white" strokeLinejoin="round" />
      {/* Worried eyes */}
      <circle cx="55" cy="44" r="3" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <circle cx="65" cy="44" r="3" stroke="#0A0A0A" strokeWidth="1.5" fill="white" />
      <circle cx="55" cy="44" r="1.2" fill="#0A0A0A" />
      <circle cx="65" cy="44" r="1.2" fill="#0A0A0A" />
      {/* Concerned brows */}
      <path d="M51 39 Q55 37 59 39" stroke="#0A0A0A" strokeWidth="1.5" fill="none" />
      <path d="M61 39 Q65 37 69 39" stroke="#0A0A0A" strokeWidth="1.5" fill="none" />
      {/* Tail down */}
      <path d="M86 80 Q88 92 80 96" stroke="#0A0A0A" strokeWidth="2" fill="none" strokeLinecap="round" />
    </>
  ),
};

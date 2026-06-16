import { useState } from "react";

/* ------------------------------------------------------------------ *
 * AssistantRoom — isometric "view all assistants" room.
 *
 * Self-contained: inline types, no dependencies beyond React. Each
 * assistant is rendered as a stylized flat-design cat placed on the
 * floor of an isometric room with static furniture.
 * ------------------------------------------------------------------ */

/* ----------------------------- Types ----------------------------- */

type CatPose = "sitting" | "standing" | "lying" | "looking-up";
type CatAccessory = "glasses" | "bow-tie" | "hat" | "scarf" | "none";

interface CatConfig {
  bodyColor: string;
  accentColor: string; // ears, nose
  accessoryColor: string;
  pose: CatPose;
  accessory: CatAccessory;
}

interface Assistant {
  id: string;
  name: string;
  model: string;
  cat: CatConfig;
  isActive: boolean;
}

interface AssistantRoomProps {
  assistants: Assistant[];
  selectedId?: string | null;
  onSelectAssistant: (id: string) => void;
}

/* ----------------------- Isometric projection -------------------- */

const ISO = {
  originX: 400,
  originY: 140,
  unitX: 3.2, // horizontal spread per logical unit
  unitY: 1.6, // vertical spread per logical unit
} as const;

/**
 * Map logical floor coordinates (0–100 scale) to screen coordinates
 * using a 2:1 isometric projection. Shared by furniture and cats so
 * everything lives in one coordinate space.
 */
function isoProject(x: number, y: number): { screenX: number; screenY: number } {
  return {
    screenX: ISO.originX + (x - y) * ISO.unitX,
    screenY: ISO.originY + (x + y) * ISO.unitY,
  };
}

/* --------------------------- Room shell -------------------------- */

const WALL_HEIGHT = 130;

function RoomShell() {
  const back = isoProject(0, 0);
  const left = isoProject(0, 100);
  const right = isoProject(100, 0);
  const front = isoProject(100, 100);

  const floorPoints = [back, right, front, left]
    .map((p) => `${p.screenX},${p.screenY}`)
    .join(" ");

  const leftWall = [
    `${back.screenX},${back.screenY}`,
    `${left.screenX},${left.screenY}`,
    `${left.screenX},${left.screenY - WALL_HEIGHT}`,
    `${back.screenX},${back.screenY - WALL_HEIGHT}`,
  ].join(" ");

  const rightWall = [
    `${back.screenX},${back.screenY}`,
    `${right.screenX},${right.screenY}`,
    `${right.screenX},${right.screenY - WALL_HEIGHT}`,
    `${back.screenX},${back.screenY - WALL_HEIGHT}`,
  ].join(" ");

  return (
    <g>
      <polygon points={leftWall} fill="#E8E0D4" stroke="#B8AD9E" strokeWidth={1} />
      <polygon points={rightWall} fill="#F2EDE6" stroke="#B8AD9E" strokeWidth={1} />
      <polygon points={floorPoints} fill="#D4C9BA" stroke="#B8AD9E" strokeWidth={1} />
    </g>
  );
}

/* -------------------------- Furniture ---------------------------- */

const ACCENT = "#C4714A"; // terracotta accent

function Desk() {
  // Left-back corner of the room.
  const p = isoProject(20, 22);
  const x = p.screenX;
  const y = p.screenY;
  const w = 30; // half-width along the iso axes
  return (
    <g>
      {/* top surface */}
      <polygon
        points={`${x},${y - 34} ${x + w},${y - 34 + w * 0.5} ${x},${y - 34 + w} ${x - w},${y - 34 + w * 0.5}`}
        fill="#A98E6F"
        stroke="#8C7457"
        strokeWidth={1}
      />
      {/* left side */}
      <polygon
        points={`${x - w},${y - 34 + w * 0.5} ${x},${y - 34 + w} ${x},${y + 6} ${x - w},${y - 24 + w * 0.5}`}
        fill="#8C7457"
        stroke="#74603F"
        strokeWidth={1}
      />
      {/* right side */}
      <polygon
        points={`${x + w},${y - 34 + w * 0.5} ${x},${y - 34 + w} ${x},${y + 6} ${x + w},${y - 24 + w * 0.5}`}
        fill="#9A8062"
        stroke="#74603F"
        strokeWidth={1}
      />
      {/* laptop on top */}
      <polygon
        points={`${x},${y - 44} ${x + 11},${y - 38} ${x},${y - 32} ${x - 11},${y - 38}`}
        fill="#3A3A3A"
        stroke="#2A2A2A"
        strokeWidth={1}
      />
      <polygon
        points={`${x - 11},${y - 38} ${x},${y - 32} ${x},${y - 48} ${x - 11},${y - 54}`}
        fill="#5C5C5C"
        stroke="#2A2A2A"
        strokeWidth={1}
      />
    </g>
  );
}

function Bookshelf() {
  // Against the left wall.
  const p = isoProject(6, 60);
  const x = p.screenX;
  const y = p.screenY;
  const spines = ["#C4714A", "#8C9A7B", "#A98E6F", "#7B8FA9", "#C4A24A"];
  return (
    <g>
      {/* shelf body — a tall iso box facing the right */}
      <polygon
        points={`${x},${y - 70} ${x + 22},${y - 59} ${x + 22},${y + 1} ${x},${y - 10}`}
        fill="#9A8062"
        stroke="#74603F"
        strokeWidth={1}
      />
      <polygon
        points={`${x},${y - 70} ${x},${y - 10} ${x - 8},${y - 14} ${x - 8},${y - 74}`}
        fill="#74603F"
        stroke="#5E4D33"
        strokeWidth={1}
      />
      {/* 3 shelves with colorful book spines */}
      {[0, 1, 2].map((row) => {
        const sy = y - 58 + row * 20;
        return spines.slice(0, 5).map((c, i) => (
          <rect
            key={`${row}-${i}`}
            x={x + 3 + i * 3.6}
            y={sy - i * 1.5}
            width={3}
            height={13}
            fill={c}
            stroke="#5E4D33"
            strokeWidth={0.5}
          />
        ));
      })}
    </g>
  );
}

function FloorLamp() {
  // Right-back corner.
  const p = isoProject(84, 16);
  const x = p.screenX;
  const y = p.screenY;
  return (
    <g>
      {/* base */}
      <ellipse cx={x} cy={y} rx={10} ry={5} fill="#8C7457" stroke="#74603F" strokeWidth={1} />
      {/* pole */}
      <rect x={x - 1.5} y={y - 86} width={3} height={86} fill="#74603F" />
      {/* round shade */}
      <ellipse cx={x} cy={y - 92} rx={16} ry={11} fill="#F2EDE6" stroke="#B8AD9E" strokeWidth={1} />
      <path d={`M${x - 16},${y - 92} Q${x},${y - 82} ${x + 16},${y - 92}`} fill="#E8DFCE" />
    </g>
  );
}

function Rug() {
  // Floor center — octagonal with a simple geometric pattern.
  const c = isoProject(52, 58);
  const cx = c.screenX;
  const cy = c.screenY;
  const rx = 78;
  const ry = 39;
  const oct = (sx: number, sy: number) =>
    [
      [-0.5, -1],
      [0.5, -1],
      [1, 0],
      [0.5, 1],
      [-0.5, 1],
      [-1, 0],
    ]
      .map(([dx, dy]) => `${cx + dx * sx},${cy + dy * sy}`)
      .join(" ");
  return (
    <g>
      <polygon points={oct(rx, ry)} fill="#C9BCA8" stroke="#B8AD9E" strokeWidth={1} />
      <polygon points={oct(rx * 0.66, ry * 0.66)} fill="#D8CDBA" stroke="#B8AD9E" strokeWidth={1} />
      <polygon points={oct(rx * 0.32, ry * 0.32)} fill={ACCENT} opacity={0.45} stroke="#B8AD9E" strokeWidth={1} />
    </g>
  );
}

function PottedPlant() {
  // Right wall, front.
  const p = isoProject(86, 82);
  const x = p.screenX;
  const y = p.screenY;
  return (
    <g>
      {/* pot */}
      <polygon
        points={`${x - 11},${y - 14} ${x + 11},${y - 14} ${x + 8},${y} ${x - 8},${y}`}
        fill={ACCENT}
        stroke="#9A5536"
        strokeWidth={1}
      />
      <ellipse cx={x} cy={y - 14} rx={11} ry={4} fill="#D88A63" stroke="#9A5536" strokeWidth={1} />
      {/* abstract leaves */}
      <path d={`M${x},${y - 14} Q${x - 18},${y - 30} ${x - 6},${y - 46}`} fill="none" stroke="#6E7E5C" strokeWidth={4} strokeLinecap="round" />
      <path d={`M${x},${y - 14} Q${x + 16},${y - 28} ${x + 8},${y - 48}`} fill="none" stroke="#7E8E68" strokeWidth={4} strokeLinecap="round" />
      <path d={`M${x},${y - 14} Q${x},${y - 36} ${x + 2},${y - 52}`} fill="none" stroke="#8C9A7B" strokeWidth={4} strokeLinecap="round" />
      <ellipse cx={x - 6} cy={y - 46} rx={6} ry={9} fill="#8C9A7B" transform={`rotate(-20 ${x - 6} ${y - 46})`} />
      <ellipse cx={x + 8} cy={y - 48} rx={6} ry={9} fill="#6E7E5C" transform={`rotate(18 ${x + 8} ${y - 48})`} />
      <ellipse cx={x + 2} cy={y - 52} rx={5} ry={8} fill="#7E8E68" />
    </g>
  );
}

function RoomDecorations() {
  return (
    <g>
      <Rug />
      <Desk />
      <Bookshelf />
      <FloorLamp />
      <PottedPlant />
    </g>
  );
}

/* ----------------------------- Cat ------------------------------- *
 * Drawn in a local coordinate space where (0, 0) is the cat's base
 * (between its feet); the cat extends upward into negative y.
 * ----------------------------------------------------------------- */

interface HeadPos {
  hx: number;
  hy: number;
  r: number;
}

const HEAD_BY_POSE: Record<CatPose, HeadPos> = {
  sitting: { hx: 0, hy: -46, r: 15 },
  "looking-up": { hx: 0, hy: -48, r: 15 },
  standing: { hx: 23, hy: -30, r: 13 },
  lying: { hx: -25, hy: -16, r: 13 },
};

function CatBody({ cat }: { cat: CatConfig }) {
  const { bodyColor, pose } = cat;
  const tail = { fill: "none", stroke: bodyColor, strokeWidth: 6, strokeLinecap: "round" as const };

  switch (pose) {
    case "standing":
      return (
        <g>
          {/* legs */}
          <ellipse cx={-14} cy={-6} rx={4} ry={8} fill={bodyColor} />
          <ellipse cx={-2} cy={-5} rx={4} ry={8} fill={bodyColor} />
          <ellipse cx={10} cy={-5} rx={4} ry={8} fill={bodyColor} />
          <ellipse cx={20} cy={-6} rx={4} ry={8} fill={bodyColor} />
          {/* horizontal body */}
          <ellipse cx={2} cy={-20} rx={26} ry={14} fill={bodyColor} />
          <path d={`M-24,-22 Q-40,-30 -32,-46`} {...tail} />
        </g>
      );
    case "lying":
      return (
        <g>
          <ellipse cx={0} cy={-10} rx={31} ry={12} fill={bodyColor} />
          <path d={`M28,-12 Q46,-12 44,-2`} {...tail} />
        </g>
      );
    case "sitting":
    case "looking-up":
    default:
      return (
        <g>
          <ellipse cx={0} cy={-18} rx={21} ry={25} fill={bodyColor} />
          {/* curled tail to the side */}
          <path d={`M18,-6 Q40,-4 34,-24 Q31,-32 22,-28`} {...tail} />
        </g>
      );
  }
}

function CatHead({ cat }: { cat: CatConfig }) {
  const { bodyColor, accentColor, pose } = cat;
  const { hx, hy, r } = HEAD_BY_POSE[pose];
  const lookUp = pose === "looking-up";
  const eyeY = hy + (lookUp ? -4 : -1);
  const pupilY = eyeY + (lookUp ? -1 : 0);
  const tilt = lookUp ? -15 : 0;

  return (
    <g transform={`rotate(${tilt} ${hx} ${hy})`}>
      {/* ears */}
      <polygon
        points={`${hx - r * 0.75},${hy - r * 0.55} ${hx - r * 0.2},${hy - r * 1.35} ${hx + r * 0.05},${hy - r * 0.7}`}
        fill={accentColor}
        stroke={bodyColor}
        strokeWidth={1}
      />
      <polygon
        points={`${hx + r * 0.75},${hy - r * 0.55} ${hx + r * 0.2},${hy - r * 1.35} ${hx - r * 0.05},${hy - r * 0.7}`}
        fill={accentColor}
        stroke={bodyColor}
        strokeWidth={1}
      />
      {/* head */}
      <circle cx={hx} cy={hy} r={r} fill={bodyColor} />
      {/* eyes */}
      <circle cx={hx - 6} cy={eyeY} r={3} fill="#2C2C2C" />
      <circle cx={hx + 6} cy={eyeY} r={3} fill="#2C2C2C" />
      <circle cx={hx - 5} cy={pupilY - 1} r={1} fill="#FFFFFF" />
      <circle cx={hx + 7} cy={pupilY - 1} r={1} fill="#FFFFFF" />
      {/* nose */}
      <polygon
        points={`${hx - 2.5},${hy + 5} ${hx + 2.5},${hy + 5} ${hx},${hy + 8}`}
        fill={accentColor}
      />
    </g>
  );
}

function CatAccessoryLayer({ cat }: { cat: CatConfig }) {
  const { accessory, accessoryColor, pose } = cat;
  const { hx, hy, r } = HEAD_BY_POSE[pose];

  switch (accessory) {
    case "glasses":
      return (
        <g fill="none" stroke={accessoryColor} strokeWidth={1.5}>
          <circle cx={hx - 6} cy={hy - 1} r={4} />
          <circle cx={hx + 6} cy={hy - 1} r={4} />
          <line x1={hx - 2} y1={hy - 1} x2={hx + 2} y2={hy - 1} />
        </g>
      );
    case "bow-tie":
      return (
        <g fill={accessoryColor}>
          <polygon points={`${hx},${hy + r} ${hx - 8},${hy + r - 4} ${hx - 8},${hy + r + 4}`} />
          <polygon points={`${hx},${hy + r} ${hx + 8},${hy + r - 4} ${hx + 8},${hy + r + 4}`} />
          <circle cx={hx} cy={hy + r} r={2} />
        </g>
      );
    case "hat":
      return (
        <g fill={accessoryColor}>
          <rect x={hx - 14} y={hy - r - 2} width={28} height={4} rx={1} />
          <rect x={hx - 8} y={hy - r - 14} width={16} height={13} rx={1} />
        </g>
      );
    case "scarf":
      return (
        <path
          d={`M${hx - r},${hy + r - 2} Q${hx - 4},${hy + r + 4} ${hx + r},${hy + r - 2}`}
          fill="none"
          stroke={accessoryColor}
          strokeWidth={5}
          strokeLinecap="round"
        />
      );
    case "none":
    default:
      return null;
  }
}

function Cat({ cat }: { cat: CatConfig }) {
  return (
    <g>
      <CatBody cat={cat} />
      <CatHead cat={cat} />
      <CatAccessoryLayer cat={cat} />
    </g>
  );
}

/* ------------------------ Cat placement -------------------------- */

interface CatSlot {
  assistant: Assistant;
  screenX: number;
  screenY: number;
  depth: number;
}

function layoutAssistants(assistants: Assistant[]): CatSlot[] {
  const n = assistants.length;
  const baseY = 60;
  const spacing = 26;
  return assistants
    .map((assistant, i) => {
      const lx = 52 + (i - (n - 1) / 2) * spacing;
      const { screenX, screenY } = isoProject(lx, baseY);
      return { assistant, screenX, screenY, depth: lx + baseY };
    })
    // Draw back-to-front so nearer cats overlap farther ones.
    .sort((a, b) => a.depth - b.depth);
}

interface CatFigureProps {
  assistant: Assistant;
  screenX: number;
  screenY: number;
  isSelected: boolean;
  onSelect: (id: string) => void;
}

function CatFigure({ assistant, screenX, screenY, isSelected, onSelect }: CatFigureProps) {
  const [hovered, setHovered] = useState(false);
  const showRing = assistant.isActive || isSelected;

  return (
    <g
      transform={`translate(${screenX} ${screenY}) scale(${hovered ? 1.08 : 1})`}
      style={{ transition: "transform 150ms ease-out", cursor: "pointer" }}
      onClick={() => onSelect(assistant.id)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      role="button"
      aria-label={`${assistant.name} (${assistant.model})`}
    >
      {/* drop shadow */}
      <ellipse cx={0} cy={4} rx={25} ry={8} fill="rgba(0,0,0,0.12)" />
      {/* active / selected glow ring */}
      {showRing && (
        <circle cx={0} cy={-6} r={30} fill="none" stroke={ACCENT} strokeWidth={2} opacity={0.6} />
      )}
      <Cat cat={assistant.cat} />
      {/* name + model label */}
      <text x={0} y={24} textAnchor="middle" fontSize={11} fill="#5C5049" fontFamily="system-ui">
        {assistant.name}
      </text>
      <text x={0} y={36} textAnchor="middle" fontSize={9} fill="#8A8077" fontFamily="system-ui">
        {assistant.model}
      </text>
    </g>
  );
}

/* --------------------------- Component --------------------------- */

export default function AssistantRoom({
  assistants,
  selectedId,
  onSelectAssistant,
}: AssistantRoomProps) {
  const slots = layoutAssistants(assistants);

  return (
    <svg viewBox="0 0 800 500" width="100%" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Assistant room">
      <RoomShell />
      <RoomDecorations />
      {slots.map((slot) => (
        <CatFigure
          key={slot.assistant.id}
          assistant={slot.assistant}
          screenX={slot.screenX}
          screenY={slot.screenY}
          isSelected={selectedId === slot.assistant.id}
          onSelect={onSelectAssistant}
        />
      ))}
    </svg>
  );
}

/* ---------------------------- Demo ------------------------------- */

const DEMO_ASSISTANTS: Assistant[] = [
  {
    id: "aria",
    name: "Aria",
    model: "GPT-4o",
    isActive: true,
    cat: {
      bodyColor: "#E8C9A0",
      accentColor: "#C99A6A",
      accessoryColor: "#3A3A3A",
      pose: "sitting",
      accessory: "glasses",
    },
  },
  {
    id: "sol",
    name: "Sol",
    model: "Claude 3.5",
    isActive: false,
    cat: {
      bodyColor: "#B8C4D4",
      accentColor: "#8A9AB0",
      accessoryColor: "#C4714A",
      pose: "lying",
      accessory: "scarf",
    },
  },
  {
    id: "rex",
    name: "Rex",
    model: "Gemini 1.5",
    isActive: false,
    cat: {
      bodyColor: "#C7B0A0",
      accentColor: "#9A7E6C",
      accessoryColor: "#4A6E8C",
      pose: "standing",
      accessory: "bow-tie",
    },
  },
];

export function AssistantRoomDemo() {
  const [selectedId, setSelectedId] = useState<string | null>("aria");
  if (!import.meta.env.DEV) return null;
  return (
    <div style={{ maxWidth: 800, margin: "0 auto" }}>
      <AssistantRoom
        assistants={DEMO_ASSISTANTS}
        selectedId={selectedId}
        onSelectAssistant={(id) => setSelectedId(id)}
      />
    </div>
  );
}

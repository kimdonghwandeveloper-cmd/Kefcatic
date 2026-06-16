export function IsometricRoom({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 280 250"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden
    >
      {/* ── Floor ── */}
      <polygon points="140,118 248,172 168,218 60,164" fill="#C9B8A4" />

      {/* ── Right back wall ── */}
      <polygon points="140,118 248,172 248,86 140,32" fill="#EDE0D0" />

      {/* ── Left back wall ── */}
      <polygon points="140,118 60,164 60,78 140,32" fill="#DDD0BC" />

      {/* Window on right wall */}
      <polygon points="205,85 238,102 238,140 205,123" fill="#D4EBF5" opacity="0.55" />
      <polygon points="203,84 240,102 240,106 203,88" fill="#EDE0D0" />
      <line x1="222" y1="96" x2="222" y2="140" stroke="#EDE0D0" strokeWidth="1.5" />
      <line x1="205" y1="113" x2="238" y2="122" stroke="#EDE0D0" strokeWidth="1.5" />

      {/* Bookshelf on left wall */}
      <polygon points="94,92 128,108 128,156 94,140" fill="#A08868" />
      <polygon points="94,112 128,128 128,133 94,117" fill="#7A6248" />
      <polygon points="94,133 128,149 128,154 94,138" fill="#7A6248" />
      {/* books */}
      <polygon points="98,95 107,99 107,112 98,108" fill="#C8B898" />
      <polygon points="108,99 114,102 114,115 108,112" fill="#B8A880" />
      <polygon points="115,102 120,104 120,117 115,114" fill="#D4C4A0" />

      {/* ── Desk (x=2..5, y=0..2, z=0..2) ── */}
      {/* Desk top surface */}
      <polygon points="186,90 248,122 212,144 150,112" fill="#B09A7A" />
      {/* Desk front face (y=0) */}
      <polygon points="186,138 248,170 248,122 186,90" fill="#8A7358" />
      {/* Desk left face (x=2) */}
      <polygon points="186,138 150,160 150,112 186,90" fill="#9A8368" />

      {/* Monitor on desk */}
      <polygon points="205,102 226,113 226,132 205,121" fill="#3A3836" />
      <polygon points="208,105 223,113 223,129 208,121" fill="#C8D8E8" opacity="0.7" />
      {/* screen content */}
      <line x1="210" y1="110" x2="221" y2="115" stroke="#8090A0" strokeWidth="0.8" opacity="0.8" />
      <line x1="210" y1="115" x2="220" y2="119" stroke="#8090A0" strokeWidth="0.8" opacity="0.8" />
      <line x1="210" y1="119" x2="218" y2="123" stroke="#8090A0" strokeWidth="0.8" opacity="0.8" />
      {/* monitor stand */}
      <polygon points="214,132 218,134 218,138 214,136" fill="#2D2B29" />
      <polygon points="211,138 221,142 221,144 211,140" fill="#2D2B29" />

      {/* Desk lamp */}
      <line x1="175" y1="108" x2="182" y2="88" stroke="#2D2B29" strokeWidth="2" />
      <polygon points="168,87 186,94 184,101 166,94" fill="#F0D9B0" />
      <polygon points="173,108 180,111 180,115 173,112" fill="#2D2B29" />

      {/* Mug on desk */}
      <polygon points="155,122 163,126 163,134 155,130" fill="#FAFAF8" />
      <polygon points="163,126 167,128 167,135 163,134" fill="#E8E4DE" />

      {/* ── Plant in left corner ── */}
      <polygon points="63,171 75,177 75,183 63,177" fill="#9A8468" />
      <polygon points="61,167 77,174 75,177 63,171" fill="#8B7358" />
      <ellipse cx="68" cy="159" rx="12" ry="8" fill="#7A8C6E" />
      <ellipse cx="62" cy="153" rx="9" ry="6" fill="#8AA07E" />
      <ellipse cx="75" cy="156" rx="8" ry="5" fill="#6B7D60" />
      <ellipse cx="68" cy="149" rx="7" ry="5" fill="#7A9070" />

      {/* ── Cat sitting near desk ── */}
      {/* body */}
      <ellipse cx="162" cy="176" rx="14" ry="9" fill="#C4A882" />
      {/* head */}
      <ellipse cx="164" cy="163" rx="10" ry="9" fill="#C4A882" />
      {/* ears */}
      <polygon points="157,158 154,149 162,156" fill="#C4A882" />
      <polygon points="171,155 174,146 167,154" fill="#C4A882" />
      {/* eyes */}
      <circle cx="161" cy="163" r="1.5" fill="#5A3A20" />
      <circle cx="168" cy="162" r="1.5" fill="#5A3A20" />
      {/* nose */}
      <circle cx="164" cy="166" r="0.8" fill="#B08060" />
      {/* tail */}
      <path
        d="M174,181 Q190,170 188,158 Q186,150 180,154"
        fill="none"
        stroke="#C4A882"
        strokeWidth="3"
        strokeLinecap="round"
      />

      {/* ── Floor rug ── */}
      <polygon points="128,192 178,215 158,226 108,202" fill="#B8A898" opacity="0.45" />
    </svg>
  );
}

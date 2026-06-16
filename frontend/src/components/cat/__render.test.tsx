import { it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { writeFileSync } from "node:fs";
import AssistantRoom from "./AssistantRoom";

const assistants = [
  { id: "aria", name: "Aria", model: "GPT-4o", isActive: true,
    cat: { bodyColor:"#E8C9A0", accentColor:"#C99A6A", accessoryColor:"#3A3A3A", pose:"sitting" as const, accessory:"glasses" as const } },
  { id: "sol", name: "Sol", model: "Claude 3.5", isActive: false,
    cat: { bodyColor:"#B8C4D4", accentColor:"#8A9AB0", accessoryColor:"#C4714A", pose:"lying" as const, accessory:"scarf" as const } },
  { id: "rex", name: "Rex", model: "Gemini 1.5", isActive: false,
    cat: { bodyColor:"#C7B0A0", accentColor:"#9A7E6C", accessoryColor:"#4A6E8C", pose:"standing" as const, accessory:"bow-tie" as const } },
];

it("dump svg", () => {
  const svg = renderToStaticMarkup(<AssistantRoom assistants={assistants} selectedId="sol" onSelectAssistant={()=>{}} />);
  writeFileSync("/tmp/assistant_room.svg", svg);
});

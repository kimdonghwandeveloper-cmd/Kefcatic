import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import AssistantRoom from "./AssistantRoom";

const assistants = [
  {
    id: "aria",
    name: "Aria",
    model: "GPT-4o",
    isActive: true,
    cat: {
      bodyColor: "#E8C9A0",
      accentColor: "#C99A6A",
      accessoryColor: "#3A3A3A",
      pose: "sitting" as const,
      accessory: "glasses" as const,
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
      pose: "lying" as const,
      accessory: "scarf" as const,
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
      pose: "standing" as const,
      accessory: "bow-tie" as const,
    },
  },
];

describe("AssistantRoom", () => {
  it("renders all cats with name and model labels", () => {
    render(<AssistantRoom assistants={assistants} onSelectAssistant={() => {}} />);
    for (const a of assistants) {
      expect(screen.getByText(a.name)).toBeInTheDocument();
      expect(screen.getByText(a.model)).toBeInTheDocument();
    }
  });

  it("fires onSelectAssistant with the cat id on click", () => {
    const onSelect = vi.fn();
    render(<AssistantRoom assistants={assistants} onSelectAssistant={onSelect} />);
    fireEvent.click(screen.getByRole("button", { name: /Aria \(GPT-4o\)/ }));
    expect(onSelect).toHaveBeenCalledWith("aria");
  });

  it("shows the orange glow ring for active or selected cats", () => {
    const { container } = render(
      <AssistantRoom assistants={assistants} selectedId="sol" onSelectAssistant={() => {}} />
    );
    // Aria (isActive) + Sol (selected) => 2 rings.
    const rings = container.querySelectorAll('circle[stroke="#C4714A"]');
    expect(rings.length).toBe(2);
  });
});

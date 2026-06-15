import { useRive } from "@rive-app/react-canvas";

interface SleepyCatRiveProps {
  size: number;
}

export function SleepyCatRive({ size }: SleepyCatRiveProps) {
  const { RiveComponent } = useRive({
    src: "/assets/25457-47508-sleepy-cat-falling-asleep-loop.riv",
    autoplay: true,
  });

  return <RiveComponent style={{ width: size, height: size }} />;
}

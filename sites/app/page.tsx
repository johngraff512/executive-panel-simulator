import type { Metadata } from "next";
import { SimulatorSpike } from "./SimulatorSpike";

export const metadata: Metadata = {
  title: "Executive Panel Simulator | Feasibility Spike",
  description:
    "A Sites-native technical spike for realistic executive-panel practice.",
};

export default function Home() {
  return <SimulatorSpike />;
}

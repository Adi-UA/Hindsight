import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { StrategyPicker } from "../components/StrategyPicker";
import { renderWithChakra } from "../test-utils";

const strategies = [
  { name: "sma_crossover", description: "Trend following." },
  { name: "rsi", description: "Mean reversion." },
];

describe("StrategyPicker", () => {
  test("renders an option per strategy", () => {
    renderWithChakra(
      <StrategyPicker strategies={strategies} value="sma_crossover" onChange={() => {}} />,
    );
    expect(screen.getByRole("option", { name: "sma_crossover" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "rsi" })).toBeInTheDocument();
  });

  test("shows the selected strategy description", () => {
    renderWithChakra(
      <StrategyPicker strategies={strategies} value="rsi" onChange={() => {}} />,
    );
    expect(screen.getByText("Mean reversion.")).toBeInTheDocument();
  });

  test("calls onChange when a new strategy is picked", () => {
    const onChange = vi.fn();
    renderWithChakra(
      <StrategyPicker strategies={strategies} value="sma_crossover" onChange={onChange} />,
    );
    fireEvent.change(screen.getByLabelText("Strategy"), { target: { value: "rsi" } });
    expect(onChange).toHaveBeenCalledWith("rsi");
  });
});

import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { StrategySelect } from "../components/StrategySelect";
import { renderWithChakra } from "../test-utils";

const strategies = [
  { name: "sma_crossover", description: "Trend following." },
  { name: "rsi", description: "Mean reversion." },
  { name: "macd", description: "Momentum." },
  { name: "buy_and_hold", description: "Benchmark." },
];

describe("StrategySelect", () => {
  test("adds a strategy when clicked", () => {
    const onChange = vi.fn();
    renderWithChakra(
      <StrategySelect strategies={strategies} value={["sma_crossover"]} onChange={onChange} />,
    );
    fireEvent.click(screen.getByText("rsi"));
    expect(onChange).toHaveBeenCalledWith(["sma_crossover", "rsi"]);
  });

  test("removes an already-selected strategy", () => {
    const onChange = vi.fn();
    renderWithChakra(
      <StrategySelect
        strategies={strategies}
        value={["sma_crossover", "rsi"]}
        onChange={onChange}
      />,
    );
    fireEvent.click(screen.getByText("sma_crossover"));
    expect(onChange).toHaveBeenCalledWith(["rsi"]);
  });

  test("does not allow selecting more than max", () => {
    const onChange = vi.fn();
    renderWithChakra(
      <StrategySelect
        strategies={strategies}
        value={["sma_crossover", "rsi", "macd"]}
        onChange={onChange}
        max={3}
      />,
    );
    fireEvent.click(screen.getByText("buy_and_hold"));
    expect(onChange).not.toHaveBeenCalled();
  });
});

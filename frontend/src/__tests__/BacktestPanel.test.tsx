import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { BacktestPanel } from "../components/BacktestPanel";
import { renderWithChakra } from "../test-utils";

const strategies = [{ name: "sma_crossover", description: "Trend following." }];

describe("BacktestPanel", () => {
  test("runs the backtest with the form values on submit", () => {
    const onRun = vi.fn();
    renderWithChakra(<BacktestPanel strategies={strategies} onRun={onRun} />);
    fireEvent.click(screen.getByRole("button", { name: /run backtest/i }));
    expect(onRun).toHaveBeenCalledWith(
      expect.objectContaining({ strategy: "sma_crossover", symbol: "VOO", cash: 10000 }),
    );
  });

  test("shows an error message when one is provided", () => {
    renderWithChakra(
      <BacktestPanel strategies={strategies} onRun={() => {}} error="No price data" />,
    );
    expect(screen.getByText("No price data")).toBeInTheDocument();
  });
});

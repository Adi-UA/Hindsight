import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import type { Status } from "../api";
import { BotControl } from "../components/BotControl";
import { renderWithChakra } from "../test-utils";

const strategies = [{ name: "sma_crossover", description: "Trend following." }];

const stoppedStatus: Status = {
  running: false,
  strategy: "sma_crossover",
  symbol: "VOO",
  paper: true,
  quick_test: false,
  next_run_at: null,
  last_run_at: null,
  account: null,
};

describe("BotControl", () => {
  test("shows STOPPED and a Start button when idle", () => {
    renderWithChakra(
      <BotControl status={stoppedStatus} strategies={strategies} onStart={() => {}} onStop={() => {}} />,
    );
    expect(screen.getByText("STOPPED")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /start bot/i })).toBeInTheDocument();
  });

  test("calls onStart with the form values", () => {
    const onStart = vi.fn();
    renderWithChakra(
      <BotControl status={stoppedStatus} strategies={strategies} onStart={onStart} onStop={() => {}} />,
    );
    fireEvent.click(screen.getByRole("button", { name: /start bot/i }));
    expect(onStart).toHaveBeenCalledWith(
      expect.objectContaining({ strategy: "sma_crossover", symbol: "VOO", paper: true }),
    );
  });

  test("shows RUNNING and a Stop button when active", () => {
    renderWithChakra(
      <BotControl
        status={{ ...stoppedStatus, running: true }}
        strategies={strategies}
        onStart={() => {}}
        onStop={() => {}}
      />,
    );
    expect(screen.getByText("RUNNING")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /stop bot/i })).toBeInTheDocument();
  });
});

import { screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import type { Decision } from "../api";
import { HistoryTable } from "../components/HistoryTable";
import { renderWithChakra } from "../test-utils";

describe("HistoryTable", () => {
  test("shows an empty state when there is no history", () => {
    renderWithChakra(<HistoryTable history={[]} />);
    expect(screen.getByText(/no decisions yet/i)).toBeInTheDocument();
  });

  test("renders a row per decision", () => {
    const history: Decision[] = [
      {
        timestamp: "2024-01-02T09:30:00",
        symbol: "VOO",
        strategy: "rsi",
        signal: "BUY",
        action: "BUY",
        amount: 750,
        status: "FILLED",
      },
    ];
    renderWithChakra(<HistoryTable history={history} />);
    expect(screen.getAllByText("BUY").length).toBeGreaterThan(0);
    expect(screen.getByText("FILLED")).toBeInTheDocument();
    expect(screen.getByText("rsi")).toBeInTheDocument();
  });
});

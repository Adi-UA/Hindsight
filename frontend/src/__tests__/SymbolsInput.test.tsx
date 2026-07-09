import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { SymbolsInput } from "../components/SymbolsInput";
import { renderWithChakra } from "../test-utils";

describe("SymbolsInput", () => {
  test("adds an uppercased ticker on Enter", () => {
    const onChange = vi.fn();
    renderWithChakra(<SymbolsInput value={["VOO"]} onChange={onChange} />);
    const input = screen.getByLabelText("Add symbol");
    fireEvent.change(input, { target: { value: "qqqm" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onChange).toHaveBeenCalledWith(["VOO", "QQQM"]);
  });

  test("removes a ticker via its tag", () => {
    const onChange = vi.fn();
    renderWithChakra(<SymbolsInput value={["VOO", "QQQM"]} onChange={onChange} />);
    fireEvent.click(screen.getByLabelText("Remove VOO"));
    expect(onChange).toHaveBeenCalledWith(["QQQM"]);
  });

  test("disables the input once at max", () => {
    renderWithChakra(<SymbolsInput value={["A", "B", "C"]} onChange={() => {}} max={3} />);
    expect(screen.getByLabelText("Add symbol")).toBeDisabled();
  });
});

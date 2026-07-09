import { ChakraProvider } from "@chakra-ui/react";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";

import { theme } from "./theme";

export function renderWithChakra(ui: ReactElement) {
  return render(<ChakraProvider theme={theme}>{ui}</ChakraProvider>);
}

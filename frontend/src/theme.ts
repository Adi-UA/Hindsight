import { extendTheme, type ThemeConfig } from "@chakra-ui/react";

const config: ThemeConfig = {
  initialColorMode: "dark",
  useSystemColorMode: false,
};

export const theme = extendTheme({
  config,
  styles: {
    global: {
      body: {
        bg: "gray.900",
        color: "gray.100",
      },
    },
  },
  colors: {
    brand: {
      50: "#e6f0ff",
      100: "#bcd6ff",
      500: "#3b82f6",
      600: "#2563eb",
      700: "#1d4ed8",
    },
  },
  components: {
    Card: {
      baseStyle: {
        container: {
          bg: "gray.800",
          borderColor: "gray.700",
          borderWidth: "1px",
        },
      },
    },
  },
});

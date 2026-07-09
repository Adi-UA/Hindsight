import { Box, Select, Text } from "@chakra-ui/react";

import type { StrategyInfo } from "../api";

interface Props {
  strategies: StrategyInfo[];
  value: string;
  onChange: (value: string) => void;
  isDisabled?: boolean;
  label?: string;
}

export function StrategyPicker({
  strategies,
  value,
  onChange,
  isDisabled,
  label = "Strategy",
}: Props) {
  const selected = strategies.find((s) => s.name === value);
  return (
    <Box>
      <Text mb={1} fontSize="sm" fontWeight="semibold" color="gray.400">
        {label}
      </Text>
      <Select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        isDisabled={isDisabled}
        aria-label={label}
        bg="gray.900"
      >
        {strategies.map((s) => (
          <option key={s.name} value={s.name}>
            {s.name}
          </option>
        ))}
      </Select>
      {selected && (
        <Text mt={2} fontSize="xs" color="gray.500">
          {selected.description}
        </Text>
      )}
    </Box>
  );
}

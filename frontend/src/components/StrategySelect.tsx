import { Box, Checkbox, Stack, Text } from "@chakra-ui/react";

import type { StrategyInfo } from "../api";

interface Props {
  strategies: StrategyInfo[];
  value: string[];
  onChange: (value: string[]) => void;
  max?: number;
}

export function StrategySelect({ strategies, value, onChange, max = 3 }: Props) {
  const toggle = (name: string) => {
    if (value.includes(name)) {
      onChange(value.filter((n) => n !== name));
    } else if (value.length < max) {
      onChange([...value, name]);
    }
  };

  return (
    <Box>
      <Text mb={2} fontSize="sm" fontWeight="semibold" color="gray.400">
        Strategies (choose up to {max})
      </Text>
      <Stack spacing={2}>
        {strategies.map((s) => {
          const checked = value.includes(s.name);
          const disabled = !checked && value.length >= max;
          return (
            <Checkbox
              key={s.name}
              isChecked={checked}
              isDisabled={disabled}
              onChange={() => toggle(s.name)}
              alignItems="flex-start"
            >
              <Box>
                <Text fontWeight="600">{s.name}</Text>
                <Text fontSize="xs" color="gray.500">
                  {s.description}
                </Text>
              </Box>
            </Checkbox>
          );
        })}
      </Stack>
    </Box>
  );
}

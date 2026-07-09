import { Box, Input, Tag, TagCloseButton, TagLabel, Text, Wrap, WrapItem } from "@chakra-ui/react";
import { useState } from "react";

interface Props {
  value: string[];
  onChange: (value: string[]) => void;
  max?: number;
}

export function SymbolsInput({ value, onChange, max = 3 }: Props) {
  const [draft, setDraft] = useState("");

  const add = () => {
    const ticker = draft.trim().toUpperCase();
    if (ticker && !value.includes(ticker) && value.length < max) {
      onChange([...value, ticker]);
    }
    setDraft("");
  };

  const remove = (ticker: string) => onChange(value.filter((v) => v !== ticker));

  const full = value.length >= max;

  return (
    <Box>
      <Text mb={1} fontSize="sm" fontWeight="semibold" color="gray.400">
        Symbols (up to {max})
      </Text>
      <Input
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            add();
          }
        }}
        placeholder={full ? `Max ${max} symbols` : "Add a ticker and press Enter (e.g. QQQM)"}
        isDisabled={full}
        bg="gray.900"
        aria-label="Add symbol"
      />
      <Wrap mt={2} spacing={2}>
        {value.map((ticker) => (
          <WrapItem key={ticker}>
            <Tag colorScheme="blue" borderRadius="full">
              <TagLabel>{ticker}</TagLabel>
              <TagCloseButton onClick={() => remove(ticker)} aria-label={`Remove ${ticker}`} />
            </Tag>
          </WrapItem>
        ))}
      </Wrap>
    </Box>
  );
}

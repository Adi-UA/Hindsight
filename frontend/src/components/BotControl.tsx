import {
  Badge,
  Box,
  Button,
  Card,
  CardBody,
  CardHeader,
  Checkbox,
  Divider,
  Flex,
  FormControl,
  FormLabel,
  Heading,
  HStack,
  Input,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  Switch,
  Text,
  VStack,
} from "@chakra-ui/react";
import { useEffect, useState } from "react";

import type { StartRequest, Status, StrategyInfo } from "../api";
import { StrategyPicker } from "./StrategyPicker";

interface Props {
  status?: Status;
  strategies: StrategyInfo[];
  onStart: (req: StartRequest) => void;
  onStop: () => void;
  isBusy?: boolean;
}

function formatTime(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString();
}

export function BotControl({ status, strategies, onStart, onStop, isBusy }: Props) {
  const running = status?.running ?? false;
  const [strategy, setStrategy] = useState(status?.strategy ?? "sma_crossover");
  const [symbol, setSymbol] = useState(status?.symbol ?? "VOO");
  const [paper, setPaper] = useState(status?.paper ?? true);
  const [quickTest, setQuickTest] = useState(false);

  // Sync the form with what the server reports while the bot is stopped.
  useEffect(() => {
    if (status && !running) {
      setStrategy(status.strategy);
      setSymbol(status.symbol);
      setPaper(status.paper);
    }
  }, [status, running]);

  const account = status?.account;
  const locked = running || isBusy;

  return (
    <Card>
      <CardHeader pb={2}>
        <Flex align="center" justify="space-between">
          <Heading size="md">Bot</Heading>
          <Badge colorScheme={running ? "green" : "gray"} fontSize="0.8em">
            {running ? "RUNNING" : "STOPPED"}
          </Badge>
        </Flex>
      </CardHeader>
      <CardBody pt={0}>
        <VStack align="stretch" spacing={4}>
          <StrategyPicker
            strategies={strategies}
            value={strategy}
            onChange={setStrategy}
            isDisabled={locked}
          />
          <FormControl>
            <FormLabel fontSize="sm" color="gray.400">
              Symbol
            </FormLabel>
            <Input
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              isDisabled={locked}
              bg="gray.900"
            />
          </FormControl>
          <HStack justify="space-between">
            <FormControl display="flex" alignItems="center" w="auto">
              <FormLabel htmlFor="paper" mb={0} fontSize="sm" color="gray.400">
                Paper
              </FormLabel>
              <Switch
                id="paper"
                isChecked={paper}
                onChange={(e) => setPaper(e.target.checked)}
                isDisabled={locked}
              />
            </FormControl>
            <Checkbox
              isChecked={quickTest}
              onChange={(e) => setQuickTest(e.target.checked)}
              isDisabled={locked}
            >
              <Text fontSize="sm" color="gray.400">
                Quick test (60s)
              </Text>
            </Checkbox>
          </HStack>

          {running ? (
            <Button colorScheme="red" onClick={onStop} isLoading={isBusy}>
              Stop bot
            </Button>
          ) : (
            <Button
              colorScheme="green"
              onClick={() =>
                onStart({ strategy, symbol, paper, quick_test: quickTest })
              }
              isLoading={isBusy}
            >
              Start bot
            </Button>
          )}

          <Divider borderColor="gray.700" />

          <SimpleGrid columns={2} spacing={3}>
            <Box>
              <Text fontSize="xs" color="gray.500">
                Next run
              </Text>
              <Text fontSize="sm">{formatTime(status?.next_run_at ?? null)}</Text>
            </Box>
            <Box>
              <Text fontSize="xs" color="gray.500">
                Last run
              </Text>
              <Text fontSize="sm">{formatTime(status?.last_run_at ?? null)}</Text>
            </Box>
          </SimpleGrid>

          {account && (
            <SimpleGrid columns={2} spacing={3}>
              <Stat>
                <StatLabel color="gray.500">Cash</StatLabel>
                <StatNumber fontSize="lg">
                  ${account.cash.toLocaleString()}
                </StatNumber>
              </Stat>
              <Stat>
                <StatLabel color="gray.500">Position</StatLabel>
                <StatNumber fontSize="lg">{account.position_qty} sh</StatNumber>
              </Stat>
            </SimpleGrid>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
}

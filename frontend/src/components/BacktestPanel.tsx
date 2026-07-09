import {
  Button,
  Card,
  CardBody,
  CardHeader,
  FormControl,
  FormLabel,
  Heading,
  Input,
  SimpleGrid,
  Stat,
  StatHelpText,
  StatLabel,
  StatNumber,
  Text,
  VStack,
} from "@chakra-ui/react";
import { useState } from "react";

import type { BacktestRequest, BacktestResult, StrategyInfo } from "../api";
import { EquityChart } from "./EquityChart";
import { StrategyPicker } from "./StrategyPicker";

interface Props {
  strategies: StrategyInfo[];
  onRun: (req: BacktestRequest) => void;
  result?: BacktestResult;
  isRunning?: boolean;
  error?: string;
}

export function BacktestPanel({
  strategies,
  onRun,
  result,
  isRunning,
  error,
}: Props) {
  const [strategy, setStrategy] = useState("sma_crossover");
  const [symbol, setSymbol] = useState("VOO");
  const [start, setStart] = useState("2020-01-01");
  const [end, setEnd] = useState("2024-01-01");
  const [cash, setCash] = useState(10000);

  return (
    <Card>
      <CardHeader pb={2}>
        <Heading size="md">Backtest</Heading>
      </CardHeader>
      <CardBody pt={0}>
        <VStack align="stretch" spacing={4}>
          <StrategyPicker
            strategies={strategies}
            value={strategy}
            onChange={setStrategy}
          />
          <SimpleGrid columns={2} spacing={3}>
            <FormControl>
              <FormLabel fontSize="sm" color="gray.400">
                Symbol
              </FormLabel>
              <Input
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                bg="gray.900"
              />
            </FormControl>
            <FormControl>
              <FormLabel fontSize="sm" color="gray.400">
                Starting cash
              </FormLabel>
              <Input
                type="number"
                value={cash}
                onChange={(e) => setCash(Number(e.target.value))}
                bg="gray.900"
              />
            </FormControl>
            <FormControl>
              <FormLabel fontSize="sm" color="gray.400">
                Start
              </FormLabel>
              <Input
                type="date"
                value={start}
                onChange={(e) => setStart(e.target.value)}
                bg="gray.900"
              />
            </FormControl>
            <FormControl>
              <FormLabel fontSize="sm" color="gray.400">
                End
              </FormLabel>
              <Input
                type="date"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
                bg="gray.900"
              />
            </FormControl>
          </SimpleGrid>
          <Button
            colorScheme="brand"
            onClick={() => onRun({ strategy, symbol, start, end, cash })}
            isLoading={isRunning}
            loadingText="Running"
          >
            Run backtest
          </Button>
          {error && (
            <Text color="red.300" fontSize="sm">
              {error}
            </Text>
          )}

          {result && (
            <>
              <SimpleGrid columns={{ base: 2, md: 4 }} spacing={3}>
                <Stat>
                  <StatLabel color="gray.500">Final value</StatLabel>
                  <StatNumber fontSize="lg">
                    ${result.final_value.toLocaleString()}
                  </StatNumber>
                </Stat>
                <Stat>
                  <StatLabel color="gray.500">Return</StatLabel>
                  <StatNumber
                    fontSize="lg"
                    color={result.return_pct >= 0 ? "green.300" : "red.300"}
                  >
                    {result.return_pct}%
                  </StatNumber>
                </Stat>
                <Stat>
                  <StatLabel color="gray.500">Trades</StatLabel>
                  <StatNumber fontSize="lg">{result.num_trades}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel color="gray.500">Max drawdown</StatLabel>
                  <StatNumber fontSize="lg">{result.max_drawdown_pct}%</StatNumber>
                  <StatHelpText>{result.strategy}</StatHelpText>
                </Stat>
              </SimpleGrid>
              <EquityChart series={result.series} markers={result.markers} />
            </>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
}

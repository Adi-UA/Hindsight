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
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  VStack,
} from "@chakra-ui/react";
import { useEffect, useState } from "react";

import type { BacktestRequest, ComparisonResult, StrategyInfo } from "../api";
import { ComparisonChart } from "./ComparisonChart";
import { StrategyPicker } from "./StrategyPicker";
import { SymbolsInput } from "./SymbolsInput";

const today = () => new Date().toISOString().slice(0, 10);

const twoYearsAgo = () => {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 2);
  return d.toISOString().slice(0, 10);
};

interface Props {
  strategies: StrategyInfo[];
  onRun: (req: BacktestRequest) => void;
  result?: ComparisonResult;
  isRunning?: boolean;
  error?: string;
}

export function BacktestPanel({ strategies, onRun, result, isRunning, error }: Props) {
  const [strategy, setStrategy] = useState("sma_crossover");
  const [symbols, setSymbols] = useState<string[]>(["VOO", "QQQM", "AMZN"]);
  const [start, setStart] = useState(twoYearsAgo());
  const [end, setEnd] = useState(today());
  const [cash, setCash] = useState(10000);

  // Populate the landing page with a default comparison on first load.
  useEffect(() => {
    onRun({ strategy, symbols, start, end, cash });
    // Intentionally run only once on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Card>
      <CardHeader pb={2}>
        <Heading size="md">Backtest</Heading>
      </CardHeader>
      <CardBody pt={0}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onRun({ strategy, symbols, start, end, cash });
          }}
        >
          <VStack align="stretch" spacing={4}>
            <StrategyPicker strategies={strategies} value={strategy} onChange={setStrategy} />
            <SymbolsInput value={symbols} onChange={setSymbols} />
            <SimpleGrid columns={{ base: 1, sm: 3 }} spacing={3}>
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
            </SimpleGrid>
            <Button
              type="submit"
              colorScheme="blue"
              size="lg"
              w="full"
              isLoading={isRunning}
              loadingText="Running"
              isDisabled={symbols.length === 0}
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
                <Text fontSize="sm" color="gray.400">
                  {result.strategy} · starting cash ${result.initial_cash.toLocaleString()}
                </Text>
                <TableContainer>
                  <Table size="sm" variant="simple">
                    <Thead>
                      <Tr>
                        <Th>Symbol</Th>
                        <Th isNumeric>Final value</Th>
                        <Th isNumeric>Return</Th>
                        <Th isNumeric>Trades</Th>
                        <Th isNumeric>Max DD</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {result.results.map((r) => (
                        <Tr key={r.symbol}>
                          <Td>{r.symbol}</Td>
                          <Td isNumeric>${r.final_value.toLocaleString()}</Td>
                          <Td isNumeric color={r.return_pct >= 0 ? "green.300" : "red.300"}>
                            {r.return_pct}%
                          </Td>
                          <Td isNumeric>{r.num_trades}</Td>
                          <Td isNumeric>{r.max_drawdown_pct}%</Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                </TableContainer>
                <ComparisonChart results={result.results} />
              </>
            )}
          </VStack>
        </form>
      </CardBody>
    </Card>
  );
}

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
import { useState } from "react";

import type { BacktestRequest, ComparisonResult, StrategyInfo } from "../api";
import { ComparisonChart } from "./ComparisonChart";
import { StrategySelect } from "./StrategySelect";

interface Props {
  strategies: StrategyInfo[];
  onRun: (req: BacktestRequest) => void;
  result?: ComparisonResult;
  isRunning?: boolean;
  error?: string;
}

export function BacktestPanel({ strategies, onRun, result, isRunning, error }: Props) {
  const [selected, setSelected] = useState<string[]>(["sma_crossover"]);
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
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onRun({ strategies: selected, symbol, start, end, cash });
          }}
        >
          <VStack align="stretch" spacing={4}>
            <StrategySelect strategies={strategies} value={selected} onChange={setSelected} />
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
              type="submit"
              colorScheme="blue"
              size="lg"
              w="full"
              isLoading={isRunning}
              loadingText="Running"
              isDisabled={selected.length === 0}
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
                <TableContainer>
                  <Table size="sm" variant="simple">
                    <Thead>
                      <Tr>
                        <Th>Strategy</Th>
                        <Th isNumeric>Final value</Th>
                        <Th isNumeric>Return</Th>
                        <Th isNumeric>Trades</Th>
                        <Th isNumeric>Max DD</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {result.results.map((r) => (
                        <Tr key={r.strategy}>
                          <Td>{r.strategy}</Td>
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

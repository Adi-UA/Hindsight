import {
  Box,
  Container,
  Flex,
  Heading,
  Link,
  SimpleGrid,
  Spinner,
  Text,
  useToast,
} from "@chakra-ui/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  type BacktestRequest,
  type BacktestResult,
  type StartRequest,
  getHistory,
  getStatus,
  getStrategies,
  runBacktest,
  startTrader,
  stopTrader,
} from "./api";
import { BacktestPanel } from "./components/BacktestPanel";
import { BotControl } from "./components/BotControl";
import { HistoryTable } from "./components/HistoryTable";
import { REPO_URL } from "./constants";

export default function App() {
  const queryClient = useQueryClient();
  const toast = useToast();

  const strategies = useQuery({ queryKey: ["strategies"], queryFn: getStrategies });
  const status = useQuery({
    queryKey: ["status"],
    queryFn: getStatus,
    refetchInterval: 4000,
  });
  const history = useQuery({
    queryKey: ["history"],
    queryFn: getHistory,
    refetchInterval: 4000,
  });

  const invalidateLive = () => {
    queryClient.invalidateQueries({ queryKey: ["status"] });
    queryClient.invalidateQueries({ queryKey: ["history"] });
  };

  const start = useMutation({
    mutationFn: (req: StartRequest) => startTrader(req),
    onSuccess: invalidateLive,
    onError: (e: Error) =>
      toast({ title: "Could not start bot", description: e.message, status: "error" }),
  });
  const stop = useMutation({
    mutationFn: stopTrader,
    onSuccess: invalidateLive,
    onError: (e: Error) =>
      toast({ title: "Could not stop bot", description: e.message, status: "error" }),
  });
  const backtest = useMutation<BacktestResult, Error, BacktestRequest>({
    mutationFn: (req) => runBacktest(req),
  });

  if (strategies.isLoading) {
    return (
      <Flex h="100vh" align="center" justify="center">
        <Spinner size="xl" />
      </Flex>
    );
  }

  const strategyList = strategies.data ?? [];

  return (
    <Container maxW="7xl" py={8}>
      <Flex align="center" justify="space-between" mb={6}>
        <Box>
          <Heading size="lg">SimpleTrader</Heading>
          <Text color="gray.500" fontSize="sm">
            Local dashboard for a paper-trading bot
          </Text>
        </Box>
        <Link href={REPO_URL} isExternal color="brand.500" fontSize="sm">
          GitHub
        </Link>
      </Flex>

      <SimpleGrid columns={{ base: 1, lg: 3 }} spacing={6}>
        <Box>
          <BotControl
            status={status.data}
            strategies={strategyList}
            onStart={start.mutate}
            onStop={() => stop.mutate()}
            isBusy={start.isPending || stop.isPending}
          />
        </Box>
        <Box gridColumn={{ lg: "span 2" }}>
          <BacktestPanel
            strategies={strategyList}
            onRun={backtest.mutate}
            result={backtest.data}
            isRunning={backtest.isPending}
            error={backtest.error?.message}
          />
        </Box>
      </SimpleGrid>

      <Box mt={6}>
        <HistoryTable history={history.data ?? []} />
      </Box>
    </Container>
  );
}

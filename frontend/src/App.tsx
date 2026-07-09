import { Box, Container, Flex, Heading, Link, Spinner, Text } from "@chakra-ui/react";
import { useMutation, useQuery } from "@tanstack/react-query";

import {
  type BacktestRequest,
  type ComparisonResult,
  getStrategies,
  runBacktest,
} from "./api";
import { BacktestPanel } from "./components/BacktestPanel";
import { REPO_URL } from "./constants";

export default function App() {
  const strategies = useQuery({ queryKey: ["strategies"], queryFn: getStrategies });
  const backtest = useMutation<ComparisonResult, Error, BacktestRequest>({
    mutationFn: (req) => runBacktest(req),
  });

  if (strategies.isLoading) {
    return (
      <Flex h="100vh" align="center" justify="center">
        <Spinner size="xl" />
      </Flex>
    );
  }

  return (
    <Container maxW="5xl" py={10}>
      <Box textAlign="center" mb={8}>
        <Heading size="xl">SimpleTrader</Heading>
        <Text color="gray.400" mt={2} maxW="2xl" mx="auto">
          See what would have happened. Backtest classic trading strategies on any
          stock and compare them against simply buying and holding.
        </Text>
        <Link href={REPO_URL} isExternal color="brand.500" fontSize="sm">
          GitHub
        </Link>
      </Box>

      <BacktestPanel
        strategies={strategies.data ?? []}
        onRun={backtest.mutate}
        result={backtest.data}
        isRunning={backtest.isPending}
        error={backtest.error?.message}
      />
    </Container>
  );
}

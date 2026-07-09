import {
  Badge,
  Card,
  CardBody,
  CardHeader,
  Heading,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from "@chakra-ui/react";

import type { Decision } from "../api";
import { SIGNAL_COLOR, STATUS_COLOR } from "../constants";

export function HistoryTable({ history }: { history: Decision[] }) {
  return (
    <Card>
      <CardHeader pb={2}>
        <Heading size="md">Decision history</Heading>
      </CardHeader>
      <CardBody pt={0}>
        {history.length === 0 ? (
          <Text color="gray.500" fontSize="sm">
            No decisions yet. Start the bot to see its activity here.
          </Text>
        ) : (
          <TableContainer>
            <Table size="sm" variant="simple">
              <Thead>
                <Tr>
                  <Th>Time</Th>
                  <Th>Strategy</Th>
                  <Th>Signal</Th>
                  <Th>Action</Th>
                  <Th isNumeric>Amount</Th>
                  <Th>Status</Th>
                </Tr>
              </Thead>
              <Tbody>
                {history
                  .slice()
                  .reverse()
                  .map((d, i) => (
                    <Tr key={`${d.timestamp}-${i}`}>
                      <Td whiteSpace="nowrap">
                        {new Date(d.timestamp).toLocaleString()}
                      </Td>
                      <Td>{d.strategy}</Td>
                      <Td>
                        <Badge colorScheme={SIGNAL_COLOR[d.signal] ?? "gray"}>
                          {d.signal}
                        </Badge>
                      </Td>
                      <Td>{d.action}</Td>
                      <Td isNumeric>{d.amount ?? "—"}</Td>
                      <Td>
                        <Badge colorScheme={STATUS_COLOR[d.status] ?? "gray"}>
                          {d.status}
                        </Badge>
                      </Td>
                    </Tr>
                  ))}
              </Tbody>
            </Table>
          </TableContainer>
        )}
      </CardBody>
    </Card>
  );
}

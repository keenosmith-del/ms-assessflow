import { useApi } from "../../hooks/useApi";
import { PageHeading, Panel, DataState } from "../../components/ui/UI";
import RequestTable from "../../components/requests/RequestTable";
import "./Approvals.css";
export default function Approvals() {
  const state = useApi("/v1/approvals");
  return (
    <div className="approvals-page">
      <PageHeading
        eyebrow="GOVERNANCE / APPROVALS"
        title="Decisions need a human."
        description="Your assigned requests, with policy evidence ready for review."
      />
      <Panel title="Pending your review">
        <DataState loading={state.loading} error={state.error}>
          <RequestTable items={state.data?.items} />
        </DataState>
      </Panel>
      <p className="approval-guidance">
        Open a request to review evidence and supply a decision reason.
        Requesters cannot approve their own access.
      </p>
    </div>
  );
}

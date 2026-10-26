import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { Badge, Empty, titleCase } from "../ui/UI";
import "./RequestTable.css";
export default function RequestTable({ items = [] }) {
  if (!items.length)
    return (
      <Empty title="Your request queue is clear">
        Submit an access request to start a policy-backed review.
      </Empty>
    );
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Request / application</th>
            <th>Requester</th>
            <th>Access level</th>
            <th>Status</th>
            <th>Created</th>
            <th>
              <span className="sr-only">Open</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>
                <Link to={`/requests/${item.id}`} className="request-title">
                  {titleCase(item.application_id.replaceAll("-", " "))}
                  <small>AF–{item.id.slice(0, 8).toUpperCase()}</small>
                </Link>
              </td>
              <td>{titleCase(item.requester_id)}</td>
              <td>{titleCase(item.access_level)}</td>
              <td>
                <Badge status={item.status} />
              </td>
              <td className="subtle">
                {new Date(item.created_at).toLocaleDateString()}
              </td>
              <td>
                <Link
                  aria-label={`Open request ${item.id.slice(0, 8)}`}
                  to={`/requests/${item.id}`}
                >
                  <ArrowUpRight size={17} />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

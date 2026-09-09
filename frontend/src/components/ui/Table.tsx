import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "../../lib/utils";

interface TableProps extends HTMLAttributes<HTMLTableElement> {
  headers: string[];
  children: ReactNode;
}

export function Table({ headers, children, className, ...props }: TableProps) {
  return (
    <div className="overflow-x-auto">
      <table
        className={cn("ds-table", className)}
        {...props}
      >
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header} scope="col">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export function TableRow({
  className,
  ...props
}: HTMLAttributes<HTMLTableRowElement>) {
  return <tr className={className} {...props} />;
}

export function TableCell({
  className,
  ...props
}: HTMLAttributes<HTMLTableCellElement>) {
  return <td className={className} {...props} />;
}

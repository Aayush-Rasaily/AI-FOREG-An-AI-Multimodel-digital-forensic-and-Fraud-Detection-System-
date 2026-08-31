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
        className={cn("w-full border-collapse text-left text-sm", className)}
        {...props}
      >
        <thead>
          <tr className="border-b border-slate-800 text-[11px] uppercase tracking-wider text-slate-500">
            {headers.map((header) => (
              <th className="px-4 py-3 font-medium" key={header} scope="col">
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


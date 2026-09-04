import { Input } from "../ui/Input";
import { Select } from "../ui/Select";

interface GraphFiltersProps {
  search: string;
  entityType: string;
  types: string[];
  onSearchChange: (value: string) => void;
  onTypeChange: (value: string) => void;
}

export function GraphFilters({
  search,
  entityType,
  types,
  onSearchChange,
  onTypeChange,
}: GraphFiltersProps) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <label className="block text-xs text-slate-400">
        Search
        <Input
          className="mt-1 w-56"
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Name, key, or id"
          value={search}
        />
      </label>
      <label className="block text-xs text-slate-400">
        Entity type
        <Select
          className="mt-1 w-48"
          onChange={(event) => onTypeChange(event.target.value)}
          value={entityType}
        >
          <option value="all">All types</option>
          {types.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </Select>
      </label>
    </div>
  );
}

import type { LucideIcon, LucideProps } from "lucide-react";
import {
  AlertCircle,
  Archive,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  Clock3,
  FileCheck2,
  FileType2,
  FolderOpen,
  Info,
  LayoutDashboard,
  Menu,
  Package,
  PenTool,
  Plus,
  Search,
  Settings2,
  ShieldCheck,
  Type,
  UploadCloud,
  Zap,
} from "lucide-react";

const icons = {
  "layout-dashboard": LayoutDashboard,
  "folder-open": FolderOpen,
  "pen-tool": PenTool,
  "shield-check": ShieldCheck,
  package: Package,
  "settings-2": Settings2,
  "circle-help": CircleHelp,
  "arrow-up-right": ArrowUpRight,
  "chevron-right": ChevronRight,
  search: Search,
  menu: Menu,
  plus: Plus,
  "arrow-right": ArrowRight,
  "arrow-left": ArrowLeft,
  check: Check,
  clock: Clock3,
  zap: Zap,
  "alert-circle": AlertCircle,
  type: Type,
  "check-circle-2": CheckCircle2,
  info: Info,
  "upload-cloud": UploadCloud,
  "arrow-down": ArrowDown,
  "file-type": FileType2,
  "file-check": FileCheck2,
  archive: Archive,
} satisfies Record<string, LucideIcon>;

export type IconName = keyof typeof icons;
type IconProps = Omit<LucideProps, "size"> & { name: IconName; size?: number };

export function Icon({ name, size = 18, ...props }: IconProps) {
  const IconComponent = icons[name];
  return <IconComponent size={size} aria-hidden="true" focusable="false" {...props} />;
}

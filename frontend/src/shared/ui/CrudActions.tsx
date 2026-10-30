import { useId, useState } from "react";
import { useTranslation } from "react-i18next";
import { DropdownMenu as DropdownMenuPrimitive } from "radix-ui";
import { MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import { Button } from "./Button";
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "./primitives/dialog";
import { Input } from "./primitives/input";
import { getError } from "../utils/errors";

type Props = {
  name: string;
  onRename?: (name: string) => Promise<unknown>;
  onDelete?: () => Promise<unknown>;
  deleteKind?: "danger" | "secondary";
  disabled?: boolean;
  className?: string;
  iconOnly?: boolean;
};

/** Localized rename/delete actions with a compact menu and explicit confirmation dialogs. */
export function CrudActions({ name, onRename, onDelete, deleteKind = "danger", disabled = false, className = "", iconOnly = false }: Props) {
  const { t } = useTranslation();
  const inputId = useId();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [renameOpen, setRenameOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [renameValue, setRenameValue] = useState(name);

  const openRename = () => {
    setRenameValue(name);
    setError("");
    setRenameOpen(true);
  };

  const openDelete = () => {
    setError("");
    setDeleteOpen(true);
  };

  const rename = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const value = renameValue.trim();
    if (!onRename || !value || value === name || disabled || busy) return;
    setBusy(true);
    setError("");
    try {
      await onRename(value);
      setRenameOpen(false);
    } catch (reason) {
      setError(getError(reason));
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (!onDelete || disabled || busy) return;
    setBusy(true);
    setError("");
    try {
      await onDelete();
      setDeleteOpen(false);
    } catch (reason) {
      setError(getError(reason));
    } finally {
      setBusy(false);
    }
  };

  return <>
    {iconOnly ? (
      <div className={`crud-actions ${className}`.trim()}>
        <DropdownMenuPrimitive.Root>
          <DropdownMenuPrimitive.Trigger asChild>
            <button className="crud-menu-trigger" type="button" aria-label={t("crud.manageItem", { name })} title={t("crud.actions")} disabled={disabled || busy}>
              <MoreHorizontal size={18} aria-hidden="true" />
            </button>
          </DropdownMenuPrimitive.Trigger>
          <DropdownMenuPrimitive.Portal>
            <DropdownMenuPrimitive.Content className="crud-menu-content" align="end" sideOffset={7}>
              {onRename && <DropdownMenuPrimitive.Item className="crud-menu-item" onSelect={openRename}><Pencil size={15} aria-hidden="true" />{t("crud.rename")}</DropdownMenuPrimitive.Item>}
              {onDelete && <DropdownMenuPrimitive.Item className="crud-menu-item is-danger" onSelect={openDelete}><Trash2 size={15} aria-hidden="true" />{t("crud.delete")}</DropdownMenuPrimitive.Item>}
            </DropdownMenuPrimitive.Content>
          </DropdownMenuPrimitive.Portal>
        </DropdownMenuPrimitive.Root>
      </div>
    ) : (
      <div className={`crud-actions ${className}`.trim()}>
        {onRename && <Button kind="secondary" className="crud-text-button" type="button" disabled={disabled || busy} onClick={openRename}><Pencil size={14} aria-hidden="true" />{t("crud.rename")}</Button>}
        {onDelete && <Button kind={deleteKind} className="crud-text-button is-danger" type="button" disabled={disabled || busy} onClick={openDelete}><Trash2 size={14} aria-hidden="true" />{t("crud.delete")}</Button>}
      </div>
    )}

    <Dialog open={renameOpen} onOpenChange={open => { if (!busy || open) setRenameOpen(open); }}>
      <DialogContent className="crud-dialog">
        <DialogHeader className="crud-dialog-header">
          <DialogTitle>{t("crud.renameDialogTitle")}</DialogTitle>
          <DialogDescription>{t("crud.renameDialogDescription", { name })}</DialogDescription>
        </DialogHeader>
        <form className="crud-dialog-form" onSubmit={event => void rename(event)}>
          <label className="crud-dialog-label" htmlFor={inputId}>{t("crud.nameLabel")}</label>
          <Input id={inputId} autoFocus value={renameValue} onChange={event => setRenameValue(event.target.value)} maxLength={120} aria-invalid={!!error} />
          {error && <p className="crud-dialog-error" role="alert">{error}</p>}
          <DialogFooter className="crud-dialog-footer">
            <DialogClose asChild><Button kind="quiet" type="button" disabled={busy}>{t("common.cancel")}</Button></DialogClose>
            <Button kind="primary" type="submit" disabled={disabled || busy || !renameValue.trim() || renameValue.trim() === name}>{busy ? t("crud.saving") : t("crud.saveName")}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>

    <Dialog open={deleteOpen} onOpenChange={open => { if (!busy || open) setDeleteOpen(open); }}>
      <DialogContent className="crud-dialog crud-delete-dialog">
        <DialogHeader className="crud-dialog-header">
          <DialogTitle>{t("crud.deleteDialogTitle", { name })}</DialogTitle>
          <DialogDescription>{t("crud.deleteDialogDescription")}</DialogDescription>
        </DialogHeader>
        {error && <p className="crud-dialog-error crud-delete-error" role="alert">{error}</p>}
        <DialogFooter className="crud-dialog-footer">
          <DialogClose asChild><Button kind="quiet" type="button" disabled={busy}>{t("common.cancel")}</Button></DialogClose>
          <Button kind="danger" type="button" disabled={disabled || busy} onClick={() => void remove()}>{busy ? t("crud.deleting") : t("crud.delete")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </>;
}

const DRIVE_FILE_SCOPE = "https://www.googleapis.com/auth/drive.file";
const DRIVE_FOLDER_MIME = "application/vnd.google-apps.folder";

const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";
const developerKey = import.meta.env.VITE_GOOGLE_API_KEY || "";
const appId = import.meta.env.VITE_GOOGLE_APP_ID || "";

type TokenResponse = { access_token?: string; expires_in?: number; error?: string; error_description?: string };
type PickerDocument = { id?: string; name?: string; url?: string; mimeType?: string };
type PickerResponse = { action?: string; docs?: PickerDocument[] };

type GoogleTokenClient = { requestAccessToken: (options?: { prompt?: string }) => void };
type GoogleGlobals = {
  accounts?: { oauth2?: { initTokenClient: (options: { client_id: string; scope: string; callback: (response: TokenResponse) => void }) => GoogleTokenClient } };
  picker?: any;
};

declare global {
  interface Window {
    gapi?: { load: (name: string, callback: { callback: () => void; onerror?: () => void }) => void };
    google?: GoogleGlobals;
  }
}

export type GoogleDriveConnection = { accessToken: string; expiresAt: number };
export type PickedDriveFolder = { id: string; name: string; url: string };

export const isGoogleDriveOAuthConfigured = Boolean(clientId);
export const isGoogleDrivePickerConfigured = isGoogleDriveOAuthConfigured && Boolean(developerKey && appId);

export async function connectGoogleDrive(): Promise<GoogleDriveConnection> {
  if (!isGoogleDriveOAuthConfigured) {
    throw new Error("Google OAuth chưa được cấu hình. Hãy thêm VITE_GOOGLE_CLIENT_ID rồi khởi động lại app.");
  }

  await loadScript("google-identity-services", "https://accounts.google.com/gsi/client");
  const oauth = window.google?.accounts?.oauth2;
  if (!oauth) throw new Error("Google OAuth chưa sẵn sàng.");
  return requestAccessToken(oauth);
}

export async function pickGoogleDriveFolder(locale: string, accessToken: string): Promise<PickedDriveFolder | null> {
  if (!isGoogleDrivePickerConfigured) {
    throw new Error("Google Picker chưa được cấu hình. Hãy thêm VITE_GOOGLE_CLIENT_ID, VITE_GOOGLE_API_KEY và VITE_GOOGLE_APP_ID rồi khởi động lại app.");
  }

  await loadScript("google-api-loader", "https://apis.google.com/js/api.js");
  const gapi = window.gapi;
  if (!gapi) throw new Error("Không tải được Google API Loader.");
  await new Promise<void>((resolve, reject) => gapi.load("picker", { callback: resolve, onerror: () => reject(new Error("Không tải được Google Picker.")) }));

  const pickerApi = window.google?.picker;
  if (!pickerApi) throw new Error("Google Picker chưa sẵn sàng.");

  return new Promise((resolve, reject) => {
    const view = new pickerApi.DocsView(pickerApi.ViewId.FOLDERS)
      .setIncludeFolders(true)
      .setSelectFolderEnabled(true)
      .setMode(pickerApi.DocsViewMode.LIST);
    const picker = new pickerApi.PickerBuilder()
      .addView(view)
      .setOAuthToken(accessToken)
      .setDeveloperKey(developerKey)
      .setAppId(appId)
      .setLocale(locale.startsWith("vi") ? "vi" : "en")
      .setCallback((response: PickerResponse) => {
        if (response.action === pickerApi.Action.LOADED) return;
        if (response.action === pickerApi.Action.CANCEL) {
          resolve(null);
          return;
        }
        if (response.action !== pickerApi.Action.PICKED) {
          reject(new Error("Google Picker không trả về kết quả chọn thư mục."));
          return;
        }
        const doc = response.docs?.[0];
        if (!doc?.id || doc.mimeType !== DRIVE_FOLDER_MIME) {
          reject(new Error("Hãy chọn một thư mục Google Drive."));
          return;
        }
        resolve({ id: doc.id, name: doc.name || "Google Drive", url: doc.url || "" });
      })
      .build();
    picker.setVisible(true);
  });
}

function requestAccessToken(oauth: NonNullable<GoogleGlobals["accounts"]>["oauth2"]): Promise<GoogleDriveConnection> {
  if (!oauth) return Promise.reject(new Error("Google OAuth chưa sẵn sàng."));
  return new Promise((resolve, reject) => {
    const tokenClient = oauth.initTokenClient({
      client_id: clientId,
      scope: DRIVE_FILE_SCOPE,
      callback: response => {
        if (response.error || !response.access_token) {
          reject(new Error(response.error_description || "Không nhận được quyền truy cập Google Drive."));
          return;
        }
        const lifetime = Number(response.expires_in);
        resolve({
          accessToken: response.access_token,
          expiresAt: Date.now() + (Number.isFinite(lifetime) && lifetime > 0 ? lifetime : 3600) * 1000,
        });
      },
    });
    tokenClient.requestAccessToken({ prompt: "select_account" });
  });
}

function loadScript(id: string, src: string): Promise<void> {
  const existing = document.getElementById(id) as HTMLScriptElement | null;
  if (existing?.dataset.loaded === "true") return Promise.resolve();
  return new Promise((resolve, reject) => {
    const script = existing || document.createElement("script");
    script.id = id;
    script.src = src;
    script.async = true;
    script.defer = true;
    script.onload = () => { script.dataset.loaded = "true"; resolve(); };
    script.onerror = () => {
      script.remove();
      reject(new Error("Không tải được thư viện Google. Kiểm tra kết nối mạng rồi thử lại."));
    };
    if (!existing) document.head.appendChild(script);
  });
}

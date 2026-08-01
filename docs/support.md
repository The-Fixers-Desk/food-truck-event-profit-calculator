# In-app support

The bundled Help Center is available at `/help` and remains useful without a
network connection. It covers the normal workflow, product concepts, local
data safety, common troubleshooting, support contact, and support boundaries.

Support begins at `contact@fixersdesk.com`. No public phone number or response
time is stated because neither is defined for the product. Installation and
launch guidance may be linked through the centralized `SUPPORT_URL`
configuration setting. When that setting is empty, the Help Center explains
that external support is not configured and keeps all local guidance usable.

`/help/support-information` returns privacy-safe metadata: app/version,
operating-system name and release, a generic local-data category, schema
version, and last successful export time. The browser adds online/offline state
and the current route when the customer chooses **Copy support information**.
The payload intentionally excludes customer content, profile data, raw paths,
database contents, stack traces, and secrets.

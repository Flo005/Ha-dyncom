# Dyn.com Dynamic DNS für Home Assistant

Home Assistant Custom-Component, die einen [Dyn.com](https://dyn.com) Dynamic-DNS-Hostnamen
automatisch auf deine aktuelle externe IP-Adresse aktualisiert – über das
Standard-[DynDNS2-Protokoll](https://help.dyn.com/remote-access-api/perform-update/).

## Funktionsweise

Die Integration sendet in regelmäßigen Abständen einen Update-Request an
`https://members.dyndns.org/nic/update`. Der `myip`-Parameter wird bewusst
weggelassen – Dyn.com ermittelt die aktuelle externe IP anhand der
Absenderadresse des Requests, sodass keine zusätzliche IP-Abfrage nötig ist.

Der Ergebnisstatus (`good`, `nochg`, Fehlercodes wie `badauth`, `notfqdn`,
`abuse`, …) sowie die zuletzt übertragene IP-Adresse werden als Sensor-Entity
in Home Assistant angezeigt.

## Installation

### Über HACS (empfohlen)

1. HACS öffnen → **Integrationen** → Menü (⋮) → **Benutzerdefinierte Repositories**
2. Dieses Repository (`https://github.com/flo005/ha-dyncom`) als Kategorie
   **Integration** hinzufügen
3. "Dyn.com Dynamic DNS" installieren und Home Assistant neu starten

### Manuell

1. Den Ordner `custom_components/dyncom` in das `custom_components`-Verzeichnis
   deiner Home-Assistant-Installation kopieren
2. Home Assistant neu starten

## Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Nach "Dyn.com" suchen
3. Hostname, Benutzername und Passwort deines Dyn.com-Kontos eingeben

Das Aktualisierungsintervall (Standard: 15 Minuten) lässt sich anschließend
über die Options des Eintrags anpassen.

## Entities

| Entity | Beschreibung |
| --- | --- |
| `sensor.<hostname>_status` | Status des letzten Updates (`Updated`, `No change`, Fehlercode) mit `ip_address` und `hostname` als Attribute |

## Fehlerbehandlung

- Ungültige Zugangsdaten (`badauth`) lösen einen Reauth-Flow in Home Assistant
  aus – Benachrichtigung öffnen und neue Zugangsdaten eingeben
- Sonstige Fehler (z. B. Netzwerkprobleme) markieren die Integration
  vorübergehend als nicht verfügbar und werden beim nächsten Intervall erneut
  versucht

## Haftungsausschluss

Dies ist eine inoffizielle, community-entwickelte Integration und steht in
keiner Verbindung zu Oracle/Dyn.

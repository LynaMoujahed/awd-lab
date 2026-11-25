[README (1).md](https://github.com/user-attachments/files/35418141/README.1.md)
# API Gateway – JobBoard (Spring Cloud Gateway Server MVC)

Mise en place d'une API Gateway qui centralise l'accès aux microservices du projet JobBoard.
La gateway est testée avec **deux approches de configuration des routes** : statique et dynamique (Eureka).

## 1. Architecture

| Service | Technologie | Port | Nom dans Eureka |
|---|---|---|---|
| eureka | Spring Boot | 8761 | – (serveur) |
| **apigateway** | Spring Cloud Gateway Server MVC | **8080** | APIGATEWAY |
| candidat | Spring Boot | 8081 | CANDIDAT |
| job | Spring Boot + MySQL | 8082 | JOB |
| meeting | Node.js | 8083 | MEETING |
| notification | Python (FastAPI) | 8084 | NOTIFICATION |
| canditature | Spring Boot | 8085 (+ 8095 pour la 2ème instance) | CANDITATURE |

Les clients appellent uniquement `http://localhost:8080`, et la gateway redirige vers le bon service.

## 2. Routes

| Route (id) | Chemin (Path) | Service cible |
|---|---|---|
| candidature | `/mic3/**` | canditature |
| candidat | `/mic1/**` | candidat |
| job | `/api/jobs/**`, `/api/categories/**` | job |
| meeting | `/api/meetings/**` | meeting |
| notification | `/api/notifications/**` | notification |

## 3. Fichiers de configuration (module `apigateway`)

| Fichier | Rôle |
|---|---|
| `application.properties` | Port, client Eureka, Actuator, logs et **profil actif** (`spring.profiles.active`) |
| `application-static.properties` | Routes en mode **statique** (`uri=http://localhost:port`) |
| `application-dynamic.properties` | Routes en mode **dynamique** (`uri=lb://NOM-DU-SERVICE`) |

Le mode se choisit avec une seule ligne dans `application.properties`, suivie d'un redémarrage de la gateway :

```properties
spring.profiles.active=static    # ou dynamic
```

## 4. Configuration statique

Chaque route déclare l'adresse (host:port) du service **en dur** dans `application-static.properties` :

```properties
spring.cloud.gateway.server.webmvc.routes[1].id=candidat
spring.cloud.gateway.server.webmvc.routes[1].uri=http://localhost:8081
spring.cloud.gateway.server.webmvc.routes[1].predicates[0]=Path=/mic1/**
```

**Caractéristiques**

- Simple à lire et à mettre en place.
- Aucune dépendance à Eureka pour trouver les services.
- Un seul serveur par route : si l'adresse ou le port change, il faut modifier le fichier et redémarrer.
- Pas de répartition de charge : seule l'instance de canditature sur le port 8085 reçoit les requêtes.

## 5. Configuration dynamique (Eureka)

Les ports ne sont plus écrits dans le fichier. La route utilise le **nom du service** enregistré dans Eureka, avec le préfixe `lb://` (load balancer) :

```properties
spring.cloud.gateway.server.webmvc.routes[1].id=candidat
spring.cloud.gateway.server.webmvc.routes[1].uri=lb://CANDIDAT
spring.cloud.gateway.server.webmvc.routes[1].predicates[0]=Path=/mic1/**
```

La gateway est un client Eureka (`eureka.client.fetch-registry=true`) : elle interroge Eureka pour obtenir les instances disponibles du service, puis répartit les appels en **round-robin**.

**Caractéristiques**

- Pas de port en dur : un service peut changer d'adresse sans modifier la gateway.
- Plusieurs instances d'un même service sont utilisées automatiquement (load balancing).
- Une instance arrêtée est retirée du registre Eureka au bout de 30 à 60 secondes.
- Les chemins (`Path=`) restent déclarés dans le fichier.

**Remarque.** La découverte automatique de routes (`spring.cloud.gateway.discovery.locator.enabled`) est documentée pour Spring Cloud Gateway WebFlux. Cette gateway est en **Server MVC** : le mode dynamique est donc réalisé avec des routes `lb://` explicites, résolues par Eureka. De même, l'endpoint `/actuator/gateway/routes` n'est pas exposé dans cette version (seuls `health` et `info` apparaissent dans `/actuator`).

## 6. Lancer le projet

Ordre de démarrage :

1. **MySQL** (XAMPP) : nécessaire pour `job` (base `job_db`).
2. **Eureka** : `EurekaApplication` → http://localhost:8761
3. Les services : `candidat`, `job`, `canditature` (IntelliJ), `meeting` et `notification` (terminal).
4. **apigateway** : `ApigatewayApplication`, en dernier.

```powershell
# meeting (Node.js)
cd ...\microservices\meeting
npm install
npm start

# notification (Python)
cd ...\microservices\notification
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8084
```

**2ème instance de canditature (port 8095)**

```powershell
cd ...\microservices\canditature
$env:JAVA_HOME="C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot"
$env:Path="$env:JAVA_HOME\bin;$env:Path"
$env:SERVER_PORT=8095
.\mvnw.cmd spring-boot:run
```

L'instance 8085 reste lancée normalement. Dans Eureka, CANDITATURE doit afficher 2 instances.

## 7. Tests

### 7.1 Services enregistrés dans Eureka

Dans http://localhost:8761, les 6 services doivent être **UP** : APIGATEWAY, CANDIDAT, CANDITATURE, JOB, MEETING, NOTIFICATION.

### 7.2 Accès via la gateway (port 8080)

```powershell
curl.exe -s -w "`nHTTP %{http_code}`n" http://localhost:8080/mic1/candidates
curl.exe -s -w "`nHTTP %{http_code}`n" http://localhost:8080/mic3/candidature/hello
curl.exe -s -w "`nHTTP %{http_code}`n" http://localhost:8080/api/jobs
curl.exe -s -w "`nHTTP %{http_code}`n" http://localhost:8080/api/meetings/hello
curl.exe -s -w "`nHTTP %{http_code}`n" http://localhost:8080/api/notifications/hello
```

Résultat attendu : `HTTP 200` pour chaque appel.

### 7.3 Comparaison avec et sans gateway

La réponse via la gateway doit être identique à la réponse directe du service.

| Service | Direct | Via la gateway |
|---|---|---|
| candidat | http://localhost:8081/mic1/candidates | http://localhost:8080/mic1/candidates |
| job | http://localhost:8082/api/jobs | http://localhost:8080/api/jobs |
| meeting | http://localhost:8083/api/meetings/hello | http://localhost:8080/api/meetings/hello |
| notification | http://localhost:8084/api/notifications/hello | http://localhost:8080/api/notifications/hello |
| canditature | http://localhost:8085/mic3/candidature/hello | http://localhost:8080/mic3/candidature/hello |

Vérification automatique :

```powershell
$paires = @(
  @("http://localhost:8081/mic1/candidates",         "http://localhost:8080/mic1/candidates"),
  @("http://localhost:8082/api/jobs",                "http://localhost:8080/api/jobs"),
  @("http://localhost:8083/api/meetings/hello",      "http://localhost:8080/api/meetings/hello"),
  @("http://localhost:8084/api/notifications/hello", "http://localhost:8080/api/notifications/hello"),
  @("http://localhost:8085/mic3/candidature/hello",  "http://localhost:8080/mic3/candidature/hello")
)
foreach ($p in $paires) {
  $direct  = curl.exe -s $p[0]
  $gateway = curl.exe -s $p[1]
  if ($direct -eq $gateway) { $r = "IDENTIQUE" } else { $r = "DIFFERENT" }
  Write-Host ("{0,-50} {1}" -f $p[1], $r)
}
```

### 7.4 Test statique

1. Mettre `spring.profiles.active=static` et redémarrer la gateway.
2. Vérifier dans la console : `The following 1 profile is active: "static"`.
3. Exécuter les tests 7.2 et 7.3.

### 7.5 Test dynamique

1. Mettre `spring.profiles.active=dynamic` et redémarrer la gateway.
2. Vérifier dans la console : `The following 1 profile is active: "dynamic"`.
3. Exécuter les tests 7.2 et 7.3.
4. Lancer la 2ème instance de canditature (section 6) et vérifier les 2 instances dans Eureka.

### 7.6 Load balancing (mode dynamique)

```powershell
1..10 | ForEach-Object { "{0,2} -> {1}" -f $_, (curl.exe -s http://localhost:8080/mic3/candidature/hello) }
```

Les réponses sont identiques (`Hello Im microservice 3!`). Pour voir quelle instance répond, ajouter dans `canditature/src/main/resources/application.properties` :

```properties
logging.level.org.springframework.web.servlet.DispatcherServlet=DEBUG
```

Après redémarrage des deux instances, les lignes `GET "/mic3/candidature/hello"` se répartissent entre les consoles 8085 et 8095.

### 7.7 Tolérance aux pannes

Arrêter l'instance 8095, attendre 30 à 60 secondes, puis relancer la boucle de 7.6 : toutes les requêtes sont servies par l'instance 8085.

## 8. Comparaison des deux approches

| Critère | Statique | Dynamique (Eureka) |
|---|---|---|
| Adresse du service | Écrite en dur (`http://localhost:8081`) | Nom du service (`lb://CANDIDAT`) |
| Changement d'adresse ou de port | Modification du fichier et redémarrage | Automatique via Eureka |
| Plusieurs instances | Non (une adresse par route) | Oui, round-robin |
| Dépendance à Eureka | Non pour le routage | Oui |
| Instance arrêtée | Erreur tant qu'elle ne revient pas | Retirée du registre, les autres répondent |
| Mise en place | Très simple | Simple, demande Eureka et un nom de service exact |

## 9. Captures d'écran

Les captures sont dans le dossier `screenshots/`.

**Configuration**
- `static-01-config.png` : `application-static.properties`
- `dynamic-01-config.png` : `application-dynamic.properties`
- `profile-static.png` / `profile-dynamic.png` : profil actif dans la console de la gateway

**Eureka**
- `eureka-6-services.png` : les 6 services en UP
- `eureka-2-instances.png` : 2 instances de CANDITATURE (8085 et 8095)

**Accès via la gateway**
- `static-02-...` et `dynamic-02-...` : un appel par service via le port 8080
- `static-comparaison.png` / `dynamic-comparaison.png` : comparaison avec et sans gateway

**Load balancing**
- `lb-boucle.png` : les 10 requêtes dans le terminal
- `lb-consoles.png` : répartition dans les consoles 8085 et 8095
- `lb-panne.png` : réponses avec une seule instance (optionnel)

## 10. Dépannage

| Symptôme | Cause probable |
|---|---|
| 404 sur `/actuator/gateway/routes` | Endpoint non disponible en Server MVC dans cette version |
| 404 sur un appel via la gateway | Chemin qui ne correspond à aucun `Path=` |
| 404 sur un service en direct | Mauvais port (voir tableau section 1) |
| 500 ou 503 via la gateway | Service arrêté ou pas encore enregistré dans Eureka (attendre 30 s) |
| JOB absent d'Eureka | MySQL arrêté ou table `job` manquante (`spring.jpa.hibernate.ddl-auto=update` ou import de `job_db.sql`) |
| Une seule instance reçoit tout | Attendre ~30 s que la gateway rafraîchisse son registre |
| `JAVA_HOME` non défini dans PowerShell | Définir `$env:JAVA_HOME` avant `mvnw.cmd` (section 6) |

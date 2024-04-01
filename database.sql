-- MySQL dump 10.13  Distrib 8.3.0, for macos12.6 (x86_64)
--
-- Host: localhost    Database: FD2024
-- ------------------------------------------------------
-- Server version	8.3.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `course_tee`
--

DROP TABLE IF EXISTS `course_tee`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `course_tee` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `teebox` varchar(10) NOT NULL,
  `rating` decimal(4,1) DEFAULT NULL,
  `slope` decimal(3,0) DEFAULT NULL,
  `active` int NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `course_tee`
--

LOCK TABLES `course_tee` WRITE;
/*!40000 ALTER TABLE `course_tee` DISABLE KEYS */;
INSERT INTO `course_tee` VALUES (2,'Forest Dunes Golf Course','I',75.2,146,1);
/*!40000 ALTER TABLE `course_tee` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `events`
--

DROP TABLE IF EXISTS `events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `events` (
  `id` int NOT NULL AUTO_INCREMENT,
  `event_name` varchar(50) NOT NULL,
  `group_id` int NOT NULL,
  `date` date NOT NULL,
  PRIMARY KEY (`id`),
  KEY `group_id` (`group_id`),
  CONSTRAINT `events_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `events`
--

LOCK TABLES `events` WRITE;
/*!40000 ALTER TABLE `events` DISABLE KEYS */;
INSERT INTO `events` VALUES (1,'tInvite 2023',1,'2023-05-26');
/*!40000 ALTER TABLE `events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `group_user_associations`
--

DROP TABLE IF EXISTS `group_user_associations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `group_user_associations` (
  `group_id` int NOT NULL,
  `user_id` int NOT NULL,
  KEY `group_id` (`group_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `group_user_associations_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`),
  CONSTRAINT `group_user_associations_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `group_user_associations`
--

LOCK TABLES `group_user_associations` WRITE;
/*!40000 ALTER TABLE `group_user_associations` DISABLE KEYS */;
INSERT INTO `group_user_associations` VALUES (1,1);
/*!40000 ALTER TABLE `group_user_associations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `groups`
--

DROP TABLE IF EXISTS `groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `groupname` varchar(50) NOT NULL,
  `hash` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `groups`
--

LOCK TABLES `groups` WRITE;
/*!40000 ALTER TABLE `groups` DISABLE KEYS */;
INSERT INTO `groups` VALUES (1,'FD','scrypt:32768:8:1$2ACHHyWk3bIHOcNy$06d02b64a0df07660ead6a317dc7dec221747f287a9f8e5a1aa1fd77be2361e591502e09eba7ababf70395bfb3f8540fe1615b8d8266cfc81b33d68f20170711');
/*!40000 ALTER TABLE `groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `handicaps`
--

DROP TABLE IF EXISTS `handicaps`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `handicaps` (
  `id` int NOT NULL AUTO_INCREMENT,
  `player_id` int NOT NULL,
  `event_id` int NOT NULL,
  `player_hcp` decimal(3,1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `player_id` (`player_id`),
  KEY `event_id` (`event_id`),
  CONSTRAINT `handicaps_ibfk_1` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`),
  CONSTRAINT `handicaps_ibfk_2` FOREIGN KEY (`event_id`) REFERENCES `events` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `handicaps`
--

LOCK TABLES `handicaps` WRITE;
/*!40000 ALTER TABLE `handicaps` DISABLE KEYS */;
INSERT INTO `handicaps` VALUES (1,1,1,-0.4),(2,2,1,0.9),(3,7,1,16.3),(4,11,1,6.2),(5,3,1,4.3),(6,4,1,10.6),(7,12,1,5.1),(8,13,1,6.2),(9,9,1,6.6),(10,10,1,2.9),(11,8,1,8.5),(12,14,1,14.6);
/*!40000 ALTER TABLE `handicaps` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `holes`
--

DROP TABLE IF EXISTS `holes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `holes` (
  `course_id` int NOT NULL,
  `hole_number` int NOT NULL,
  `par` int NOT NULL,
  `hole_hcp` int NOT NULL,
  KEY `course_id` (`course_id`),
  CONSTRAINT `holes_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `course_tee` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `holes`
--

LOCK TABLES `holes` WRITE;
/*!40000 ALTER TABLE `holes` DISABLE KEYS */;
INSERT INTO `holes` VALUES (2,1,4,15),(2,2,4,1),(2,3,3,13),(2,4,4,9),(2,5,5,5),(2,6,4,11),(2,7,5,7),(2,8,4,3),(2,9,3,17),(2,10,4,4),(2,11,3,18),(2,12,4,10),(2,13,4,14),(2,14,4,2),(2,15,5,6),(2,16,3,8),(2,17,4,16),(2,18,5,12);
/*!40000 ALTER TABLE `holes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `matches`
--

DROP TABLE IF EXISTS `matches`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `matches` (
  `id` int NOT NULL AUTO_INCREMENT,
  `match_number` int NOT NULL,
  `match_time` time DEFAULT NULL,
  `match_starting_hole` int NOT NULL DEFAULT '1',
  `round_id` int NOT NULL,
  `course_id` int NOT NULL,
  `team_a_id` int NOT NULL,
  `team_b_id` int NOT NULL,
  `status` varchar(15) NOT NULL DEFAULT 'INCOMPLETE',
  PRIMARY KEY (`id`),
  KEY `round_id` (`round_id`),
  KEY `course_id` (`course_id`),
  KEY `team_a_id` (`team_a_id`),
  KEY `team_b_id` (`team_b_id`),
  CONSTRAINT `matches_ibfk_1` FOREIGN KEY (`round_id`) REFERENCES `rounds` (`id`),
  CONSTRAINT `matches_ibfk_2` FOREIGN KEY (`course_id`) REFERENCES `course_tee` (`id`),
  CONSTRAINT `matches_ibfk_3` FOREIGN KEY (`team_a_id`) REFERENCES `teams` (`id`),
  CONSTRAINT `matches_ibfk_4` FOREIGN KEY (`team_b_id`) REFERENCES `teams` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `matches`
--

LOCK TABLES `matches` WRITE;
/*!40000 ALTER TABLE `matches` DISABLE KEYS */;
INSERT INTO `matches` VALUES (1,1,'00:00:00',1,2,2,5,6,'INCOMPLETE\r'),(2,2,'00:00:00',1,2,2,1,3,'INCOMPLETE\r'),(3,3,'00:00:00',1,2,2,2,4,'INCOMPLETE\r');
/*!40000 ALTER TABLE `matches` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `players`
--

DROP TABLE IF EXISTS `players`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players` (
  `id` int NOT NULL AUTO_INCREMENT,
  `player_name` varchar(50) NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `group_id` (`group_id`),
  CONSTRAINT `players_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `players`
--

LOCK TABLES `players` WRITE;
/*!40000 ALTER TABLE `players` DISABLE KEYS */;
INSERT INTO `players` VALUES (1,'Trevor Grigg',1),(2,'Alex Bernstein',1),(3,'Peter Curran',1),(4,'Matt Luneack',1),(7,'Don Tappan',1),(8,'Brendan Burdette',1),(9,'Chase Dehne',1),(10,'Richard Allen',1),(11,'Dan Ritterbeck',1),(12,'Jeff Owens',1),(13,'Chris Kozerski',1),(14,'Mike Rays',1);
/*!40000 ALTER TABLE `players` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rounds`
--

DROP TABLE IF EXISTS `rounds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rounds` (
  `id` int NOT NULL AUTO_INCREMENT,
  `round_number` int NOT NULL,
  `round_name` varchar(30) DEFAULT NULL,
  `event_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `event_id` (`event_id`),
  CONSTRAINT `rounds_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `events` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rounds`
--

LOCK TABLES `rounds` WRITE;
/*!40000 ALTER TABLE `rounds` DISABLE KEYS */;
INSERT INTO `rounds` VALUES (2,1,'Friday PM',1);
/*!40000 ALTER TABLE `rounds` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `scores`
--

DROP TABLE IF EXISTS `scores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `scores` (
  `match_id` int NOT NULL,
  `match_hole_number` int NOT NULL,
  `player_id` int NOT NULL,
  `score` int NOT NULL,
  KEY `match_id` (`match_id`),
  KEY `player_id` (`player_id`),
  CONSTRAINT `scores_ibfk_1` FOREIGN KEY (`match_id`) REFERENCES `matches` (`id`),
  CONSTRAINT `scores_ibfk_2` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `scores`
--

LOCK TABLES `scores` WRITE;
/*!40000 ALTER TABLE `scores` DISABLE KEYS */;
INSERT INTO `scores` VALUES (2,1,1,4),(2,2,1,3),(2,3,1,3),(2,4,1,4),(2,5,1,5),(2,6,1,3),(2,7,1,4),(2,8,1,6),(2,9,1,3),(2,10,1,4),(2,11,1,3),(2,12,1,5),(2,13,1,4),(2,14,1,4),(2,15,1,5),(2,16,1,5),(2,17,1,3),(2,18,1,5),(2,1,2,4),(2,2,2,5),(2,3,2,3),(2,4,2,4),(2,5,2,5),(2,6,2,5),(2,7,2,7),(2,8,2,4),(2,9,2,2),(2,10,2,5),(2,11,2,3),(2,12,2,3),(2,13,2,3),(2,14,2,3),(2,15,2,4),(2,16,2,4),(2,17,2,4),(2,18,2,7),(2,1,3,5),(2,2,3,4),(2,3,3,4),(2,4,3,4),(2,5,3,7),(2,6,3,6),(2,7,3,5),(2,8,3,5),(2,9,3,5),(2,10,3,3),(2,11,3,4),(2,12,3,4),(2,13,3,4),(2,14,3,4),(2,15,3,8),(2,16,3,4),(2,17,3,6),(2,18,3,6),(2,1,4,5),(2,2,4,7),(2,3,4,4),(2,4,4,5),(2,5,4,8),(2,6,4,6),(2,7,4,5),(2,8,4,5),(2,9,4,6),(2,10,4,4),(2,11,4,3),(2,12,4,4),(2,13,4,7),(2,14,4,6),(2,15,4,9),(2,16,4,4),(2,17,4,5),(2,18,4,6);
/*!40000 ALTER TABLE `scores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `team_roster`
--

DROP TABLE IF EXISTS `team_roster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_roster` (
  `team_id` int NOT NULL,
  `player_id` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `team_roster`
--

LOCK TABLES `team_roster` WRITE;
/*!40000 ALTER TABLE `team_roster` DISABLE KEYS */;
INSERT INTO `team_roster` VALUES (1,1),(1,2),(2,7),(2,11),(3,3),(3,4),(4,12),(4,13),(5,9),(5,10),(6,8),(6,14);
/*!40000 ALTER TABLE `team_roster` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `teams`
--

DROP TABLE IF EXISTS `teams`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `teams` (
  `id` int NOT NULL AUTO_INCREMENT,
  `team_name` varchar(50) NOT NULL,
  `event_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `event_id` (`event_id`),
  CONSTRAINT `teams_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `events` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `teams`
--

LOCK TABLES `teams` WRITE;
/*!40000 ALTER TABLE `teams` DISABLE KEYS */;
INSERT INTO `teams` VALUES (1,'Low Handi',1),(2,'High Handi',1),(3,'MTPB',1),(4,'Shakey Bois',1),(5,'BOHICA',1),(6,'Plumber & Trucker',1);
/*!40000 ALTER TABLE `teams` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(30) NOT NULL,
  `hash` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'trevorgrigg','scrypt:32768:8:1$YpCyI0WxCyobRs8h$36af87517df66c9bb995a82ff6fb72ebe893141a43e0e801d72610bc46494e2029fc09d8d637bcb261ca2fb1e7e5aa5baceba78764a2a0bd1827504ed24c89ba');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-03-31 21:50:50

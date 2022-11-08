-- MySQL dump 10.13  Distrib 8.0.30, for Linux (x86_64)
--
-- Host: localhost    Database: data_extraction
-- ------------------------------------------------------
-- Server version	5.5.64-MariaDB-1~trusty

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
-- Table structure for table `acte`
--

DROP TABLE IF EXISTS `acte`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `acte` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(300) NOT NULL,
  `url` varchar(500) NOT NULL,
  `path` varchar(500) NOT NULL,
  `hash` varchar(65) NOT NULL,
  `publication_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `publication_id` (`publication_id`),
  CONSTRAINT `acte_ibfk_1` FOREIGN KEY (`publication_id`) REFERENCES `publication` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `celery_taskmeta`
--

DROP TABLE IF EXISTS `celery_taskmeta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `celery_taskmeta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task_id` varchar(155) DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `result` blob,
  `date_done` datetime DEFAULT NULL,
  `traceback` text,
  `name` varchar(155) DEFAULT NULL,
  `args` blob,
  `kwargs` blob,
  `worker` varchar(155) DEFAULT NULL,
  `retries` int(11) DEFAULT NULL,
  `queue` varchar(155) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`)
) ENGINE=InnoDB AUTO_INCREMENT=62 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `celery_tasksetmeta`
--

DROP TABLE IF EXISTS `celery_tasksetmeta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `celery_tasksetmeta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `taskset_id` varchar(155) DEFAULT NULL,
  `result` blob,
  `date_done` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `taskset_id` (`taskset_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `entite_pastell_ag`
--

DROP TABLE IF EXISTS `entite_pastell_ag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `entite_pastell_ag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `siren` varchar(9) NOT NULL,
  `id_e` int(11) NOT NULL,
  `denomination` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `parametrage`
--

DROP TABLE IF EXISTS `parametrage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `parametrage` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `siren` varchar(9) NOT NULL,
  `nic` varchar(5) NOT NULL,
  `denomination` varchar(256) NOT NULL,
  `open_data_active` tinyint(1) NOT NULL DEFAULT '0',
  `publication_data_gouv_active` tinyint(1) NOT NULL DEFAULT '0',
  `publication_udata_active` tinyint(1) NOT NULL DEFAULT '0',
  `uid_data_gouv` varchar(256) DEFAULT NULL,
  `api_key_data_gouv` varchar(256) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `modified_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `siren` (`siren`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pj_acte`
--

DROP TABLE IF EXISTS `pj_acte`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pj_acte` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `url` varchar(500) NOT NULL,
  `path` varchar(500) NOT NULL,
  `hash` varchar(65) NOT NULL,
  `publication_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `publication_id` (`publication_id`),
  CONSTRAINT `pj_acte_ibfk_1` FOREIGN KEY (`publication_id`) REFERENCES `publication` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `publication`
--

DROP TABLE IF EXISTS `publication`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `publication` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `numero_de_lacte` varchar(20) NOT NULL,
  `objet` varchar(256) NOT NULL,
  `siren` varchar(9) NOT NULL,
  `publication_open_data` varchar(1) NOT NULL DEFAULT '2',
  `date_de_lacte` datetime NOT NULL,
  `classification_code` varchar(10) NOT NULL,
  `classification_nom` varchar(100) NOT NULL,
  `acte_nature` varchar(50) NOT NULL,
  `envoi_depot` varchar(50) NOT NULL,
  `date_budget` varchar(10) DEFAULT NULL,
  `est_masque` tinyint(1) NOT NULL DEFAULT '0',
  `est_supprime` tinyint(1) NOT NULL DEFAULT '0',
  `etat` varchar(1) NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL,
  `modified_at` datetime NOT NULL,
  `date_publication` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2022-08-05 14:07:20

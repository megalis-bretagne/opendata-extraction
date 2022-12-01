CREATE TABLE `mq_budget_parametres_defaultvisualisation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `localisation` varchar(100) NOT NULL,
  `titre` varchar(255) DEFAULT NULL,
  `sous_titre` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `localisation` (`localisation`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
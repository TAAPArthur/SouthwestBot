-- phpMyAdmin SQL Dump
-- version 4.7.6
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Dec 28, 2017 at 01:14 AM
-- Server version: 10.1.29-MariaDB
-- PHP Version: 7.2.0

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";

CREATE USER 'southwest'@'localhost' IDENTIFIED VIA mysql_native_password USING '***';GRANT USAGE ON *.* TO 'southwest'@'localhost' REQUIRE NONE WITH MAX_QUERIES_PER_HOUR 0 MAX_CONNECTIONS_PER_HOUR 0 MAX_UPDATES_PER_HOUR 0 MAX_USER_CONNECTIONS 0;

GRANT ALL PRIVILEGES ON `Southwest`.* TO 'southwest'@'localhost'; 


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `Southwest`
--

-- --------------------------------------------------------

--
-- Table structure for table `CheapFlights`
--

CREATE TABLE `CheapFlights` (
  `ID` int(11) NOT NULL,
  `DepartureTime` datetime NOT NULL,
  `FlightNumber` int(11) NOT NULL,
  `Price` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `UpcomingFlights`
--

CREATE TABLE `UpcomingFlights` (
  `ID` int(11) NOT NULL,
  `UserID` int(11) NOT NULL,
  `ConfirmationNumber` varchar(15) COLLATE utf8mb4_unicode_ci NOT NULL,
  `FlightNumber` int(11) NOT NULL,
  `DepartureTime` datetime NOT NULL,
  `ArrivalTime` datetime NOT NULL,
  `Title` tinytext COLLATE utf8mb4_unicode_ci NOT NULL,
  `Origin` varchar(12) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Dest` varchar(12) COLLATE utf8mb4_unicode_ci NOT NULL,
  `StartDate` tinyint(4) DEFAULT NULL,
  `EndDate` tinyint(4) DEFAULT NULL,
  `Price` decimal(5,2) DEFAULT NULL,
  `Active` tinyint(1) NOT NULL DEFAULT '1',
  `LastUpdated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `Users`
--

CREATE TABLE `Users` (
  `ID` int(11) NOT NULL,
  `Username` varchar(30) NOT NULL,
  `Password` tinytext NOT NULL,
  `FirstName` tinytext NOT NULL,
  `LastName` tinytext NOT NULL,
  `TelegramChatID` int(11) DEFAULT NULL,
  `StartDateDefaultDelta` tinyint(3) NOT NULL DEFAULT '3',
  `EndDateDefaultDelta` tinyint(3) NOT NULL DEFAULT '3',
  `PriceDelta` decimal(5,2) NOT NULL DEFAULT '10.00',
  `MinPrice` decimal(5,2) NOT NULL DEFAULT '200.00'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `CheapFlights`
--
ALTER TABLE `CheapFlights`
  ADD PRIMARY KEY (`ID`),
  ADD UNIQUE KEY `Date` (`DepartureTime`,`FlightNumber`);

--
-- Indexes for table `UpcomingFlights`
--
ALTER TABLE `UpcomingFlights`
  ADD PRIMARY KEY (`ID`),
  ADD UNIQUE KEY `UserID` (`UserID`,`FlightNumber`,`DepartureTime`);

--
-- Indexes for table `Users`
--
ALTER TABLE `Users`
  ADD PRIMARY KEY (`ID`),
  ADD UNIQUE KEY `CrunchyrollUsername` (`Username`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `CheapFlights`
--
ALTER TABLE `CheapFlights`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=283;

--
-- AUTO_INCREMENT for table `UpcomingFlights`
--
ALTER TABLE `UpcomingFlights`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `UpcomingFlights`
--
ALTER TABLE `UpcomingFlights`
  ADD CONSTRAINT `UpcomingFlights_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `Users` (`ID`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `Users`
--
ALTER TABLE `Users`
  ADD CONSTRAINT `Users_ibfk_1` FOREIGN KEY (`ID`) REFERENCES `TAAPArthur`.`Accounts` (`ID`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

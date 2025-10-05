-- MySQL dump 10.13  Distrib 8.0.35, for Win64 (x86_64)
--
-- Host: uroktime.store    Database: school_sheduller
-- ------------------------------------------------------
-- Server version	8.4.6

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
-- Table structure for table `calc_results`
--

DROP TABLE IF EXISTS `calc_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `calc_results` (
  `id` int NOT NULL AUTO_INCREMENT,
  `job_id` int NOT NULL,
  `status` varchar(255) DEFAULT NULL,
  `objective_value` double DEFAULT NULL,
  `wall_time_s` double DEFAULT NULL,
  `total_lonely_lessons` int DEFAULT NULL,
  `total_teacher_windows` int DEFAULT NULL,
  `weights_json` json DEFAULT NULL,
  `input_data_json` json DEFAULT NULL,
  `solution_maps_json` json DEFAULT NULL,
  `display_maps_json` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_calculation_results_job` (`job_id`),
  CONSTRAINT `fk_calculation_results_job` FOREIGN KEY (`job_id`) REFERENCES `core_jobs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `calc_schedule_details`
--

DROP TABLE IF EXISTS `calc_schedule_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `calc_schedule_details` (
  `id` int NOT NULL AUTO_INCREMENT,
  `job_id` int NOT NULL,
  `class_name` varchar(255) NOT NULL,
  `subject_name` varchar(255) NOT NULL,
  `teacher_name` varchar(255) NOT NULL,
  `day` varchar(50) NOT NULL,
  `period` int NOT NULL,
  `subgroup_id` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `job_id` (`job_id`),
  CONSTRAINT `calc_schedule_details_ibfk_1` FOREIGN KEY (`job_id`) REFERENCES `core_jobs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3173 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `core_jobs`
--

DROP TABLE IF EXISTS `core_jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_jobs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `jobs_user_id_fk` (`user_id`),
  CONSTRAINT `jobs_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `core_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `core_users`
--

DROP TABLE IF EXISTS `core_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `core_versions`
--

DROP TABLE IF EXISTS `core_versions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_versions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `vers_user_id_fk` (`user_id`),
  CONSTRAINT `vers_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `core_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_calculated_years`
--

DROP TABLE IF EXISTS `input_calculated_years`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_calculated_years` (
  `id` int NOT NULL AUTO_INCREMENT,
  `training_year` int DEFAULT NULL,
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `input_calculated_years_pk` (`training_year`,`version_id`),
  KEY `fk_calculated_years_version` (`version_id`),
  CONSTRAINT `fk_calculated_years_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_class_forbidden_slots`
--

DROP TABLE IF EXISTS `input_class_forbidden_slots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_class_forbidden_slots` (
  `id` int NOT NULL AUTO_INCREMENT,
  `class_id` int DEFAULT NULL,
  `day_of_week_id` int DEFAULT NULL,
  `slot_id` int DEFAULT NULL,
  `comment` varchar(255) DEFAULT NULL,
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `input_class_forbidden_slots_pk` (`class_id`,`day_of_week_id`,`slot_id`,`version_id`),
  KEY `fk_class_forbidden_slots_version` (`version_id`),
  CONSTRAINT `class_forbidden_slots_classes_id_fk` FOREIGN KEY (`class_id`) REFERENCES `input_classes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_class_forbidden_slots_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_class_slot_weight`
--

DROP TABLE IF EXISTS `input_class_slot_weight`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_class_slot_weight` (
  `id` int NOT NULL AUTO_INCREMENT,
  `class_id` int DEFAULT NULL,
  `day_of_week` int DEFAULT NULL,
  `slot_id` int DEFAULT NULL,
  `weight` double DEFAULT NULL,
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `input_class_slot_weight_pk` (`class_id`,`day_of_week`,`slot_id`,`version_id`),
  KEY `fk_class_slot_weight_version` (`version_id`),
  CONSTRAINT `class_slot_weight_classes_id_fk` FOREIGN KEY (`class_id`) REFERENCES `input_classes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_class_slot_weight_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_class_subject_day_weight`
--

DROP TABLE IF EXISTS `input_class_subject_day_weight`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_class_subject_day_weight` (
  `id` int NOT NULL AUTO_INCREMENT,
  `class_id` int DEFAULT NULL,
  `subject_id` int DEFAULT NULL,
  `day_of_week_id` int DEFAULT NULL,
  `weight` double DEFAULT NULL,
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `input_class_subject_day_weight_pk` (`class_id`,`day_of_week_id`,`subject_id`,`version_id`),
  KEY `class_subject_day_weight_subjects_id_fk` (`subject_id`),
  KEY `class_subject_day_weight_days_of_week_id_fk` (`day_of_week_id`),
  KEY `fk_class_subject_day_weight_version` (`version_id`),
  CONSTRAINT `class_subject_day_weight_classes_id_fk` FOREIGN KEY (`class_id`) REFERENCES `input_classes` (`id`),
  CONSTRAINT `class_subject_day_weight_days_of_week_id_fk` FOREIGN KEY (`day_of_week_id`) REFERENCES `input_days_of_week` (`id`),
  CONSTRAINT `class_subject_day_weight_subjects_id_fk` FOREIGN KEY (`subject_id`) REFERENCES `input_subjects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_class_subject_day_weight_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_classes`
--

DROP TABLE IF EXISTS `input_classes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_classes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(30) DEFAULT (concat(_utf8mb4'class',to_base64(random_bytes(5)))),
  `name_eng` varchar(255) DEFAULT (concat(_utf8mb4'class_',`training_year`,_utf8mb4'_',to_base64(random_bytes(5)))),
  `training_year` int DEFAULT NULL,
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `input_classes_pk` (`name_eng`,`version_id`),
  KEY `fk_classes_version` (`version_id`),
  CONSTRAINT `fk_classes_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_compatible_subject_pairs`
--

DROP TABLE IF EXISTS `input_compatible_subject_pairs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_compatible_subject_pairs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `subject1_id` int DEFAULT NULL,
  `subject2_id` int DEFAULT NULL,
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `input_compatible_subject_pairs_pk` (`subject2_id`,`subject1_id`,`version_id`),
  KEY `compatible_subject_pairs_subjects_id_fk` (`subject1_id`),
  KEY `fk_compatible_subject_pairs_version` (`version_id`),
  CONSTRAINT `compatible_subject_pairs_subjects_id_fk` FOREIGN KEY (`subject1_id`) REFERENCES `input_subjects` (`id`),
  CONSTRAINT `compatible_subject_pairs_subjects_id_fk_2` FOREIGN KEY (`subject2_id`) REFERENCES `input_subjects` (`id`),
  CONSTRAINT `fk_compatible_subject_pairs_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `chk_subjects_not_equal` CHECK ((`subject1_id` <> `subject2_id`))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_days_of_week`
--

DROP TABLE IF EXISTS `input_days_of_week`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_days_of_week` (
  `id` int NOT NULL AUTO_INCREMENT,
  `day_of_week` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_grade_daily_lesson_limits`
--

DROP TABLE IF EXISTS `input_grade_daily_lesson_limits`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_grade_daily_lesson_limits` (
  `id` int NOT NULL AUTO_INCREMENT,
  `grade_id` int DEFAULT NULL,
  `max_lessons_per_day` int DEFAULT NULL,
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `input_grade_daily_lesson_limits_pk` (`grade_id`,`version_id`),
  KEY `fk_grade_daily_lesson_limits_version` (`version_id`),
  CONSTRAINT `fk_grade_daily_lesson_limits_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_grade_subject_max_consecutive_days`
--

DROP TABLE IF EXISTS `input_grade_subject_max_consecutive_days`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_grade_subject_max_consecutive_days` (
  `id` int NOT NULL AUTO_INCREMENT,
  `grade` int DEFAULT NULL,
  `subject_id` int DEFAULT NULL,
  `max_days` int DEFAULT NULL,
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `input_grade_subject_max_consecutive_days_pk` (`grade`,`subject_id`,`version_id`),
  KEY `grade_subject_max_consecutive_days_subjects_id_fk` (`subject_id`),
  KEY `fk_grade_subject_max_consecutive_days_version` (`version_id`),
  CONSTRAINT `fk_grade_subject_max_consecutive_days_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `grade_subject_max_consecutive_days_subjects_id_fk` FOREIGN KEY (`subject_id`) REFERENCES `input_subjects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_paired_subjects`
--

DROP TABLE IF EXISTS `input_paired_subjects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_paired_subjects` (
  `id` int NOT NULL AUTO_INCREMENT,
  `paired_subject_id` int DEFAULT NULL,
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `input_paired_subjects_pk` (`paired_subject_id`,`version_id`),
  KEY `fk_paired_subjects_version` (`version_id`),
  CONSTRAINT `fk_paired_subjects_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `paired_subjects_subjects_id_fk` FOREIGN KEY (`paired_subject_id`) REFERENCES `input_subjects` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_subgroups`
--

DROP TABLE IF EXISTS `input_subgroups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_subgroups` (
  `id` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='0 - без подгрупп';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_subject_difficulties`
--

DROP TABLE IF EXISTS `input_subject_difficulties`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_subject_difficulties` (
  `id` int NOT NULL AUTO_INCREMENT,
  `subject_id` int NOT NULL,
  `grade` int NOT NULL,
  `difficulty` int NOT NULL DEFAULT '0',
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_subject_grade` (`subject_id`,`grade`,`version_id`),
  KEY `fk_subject_difficulties_version` (`version_id`),
  CONSTRAINT `fk_subject_difficulties_subject` FOREIGN KEY (`subject_id`) REFERENCES `input_subjects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_subject_difficulties_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=256 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_subject_groups`
--

DROP TABLE IF EXISTS `input_subject_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_subject_groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `subject_group_name` varchar(50) DEFAULT NULL,
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_subject_groups_version` (`version_id`),
  CONSTRAINT `fk_subject_groups_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_subjects`
--

DROP TABLE IF EXISTS `input_subjects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_subjects` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `name_eng` varchar(255) DEFAULT (concat(_utf8mb4'subj_',to_base64(random_bytes(5)))),
  `is_split_subject` bit(1) DEFAULT NULL,
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `input_subjects_pk` (`name_eng`,`version_id`),
  KEY `fk_subjects_version` (`version_id`),
  CONSTRAINT `fk_subjects_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_subjects_not_last_lesson`
--

DROP TABLE IF EXISTS `input_subjects_not_last_lesson`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_subjects_not_last_lesson` (
  `id` int NOT NULL AUTO_INCREMENT,
  `grade` int DEFAULT NULL,
  `subject_id` int DEFAULT NULL,
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `input_subjects_not_last_lesson_pk` (`subject_id`,`grade`,`version_id`),
  KEY `fk_subjects_not_last_lesson_version` (`version_id`),
  CONSTRAINT `fk_subjects_not_last_lesson_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `subjects_not_last_lesson_subjects_id_fk` FOREIGN KEY (`subject_id`) REFERENCES `input_subjects` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_synchronized_split_subjects`
--

DROP TABLE IF EXISTS `input_synchronized_split_subjects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_synchronized_split_subjects` (
  `subject_id` int DEFAULT NULL,
  `version_id` int DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `input_synchronized_split_subjects_pk` (`subject_id`,`version_id`),
  KEY `fk_synchronized_split_subjects_version` (`version_id`),
  CONSTRAINT `fk_synchronized_split_subjects_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `synchronized_split_subjects_subjects_id_fk` FOREIGN KEY (`subject_id`) REFERENCES `input_subjects` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_teacher_assignments`
--

DROP TABLE IF EXISTS `input_teacher_assignments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_teacher_assignments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `teacher_id` int DEFAULT NULL,
  `class_id` int DEFAULT NULL,
  `subject_id` int DEFAULT NULL,
  `subgroup_id` int DEFAULT NULL,
  `weekly_hours` int DEFAULT NULL,
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `input_teacher_assignments_pk` (`teacher_id`,`class_id`,`subject_id`,`subgroup_id`,`version_id`),
  KEY `teacher_assignments_classes_id_fk` (`class_id`),
  KEY `teacher_assignments_subjects_id_fk` (`subject_id`),
  KEY `teacher_assignments_subgroups_id_fk` (`subgroup_id`),
  KEY `fk_teacher_assignments_version` (`version_id`),
  CONSTRAINT `fk_teacher_assignments_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `teacher_assignments_classes_id_fk` FOREIGN KEY (`class_id`) REFERENCES `input_classes` (`id`),
  CONSTRAINT `teacher_assignments_subgroups_id_fk` FOREIGN KEY (`subgroup_id`) REFERENCES `input_subgroups` (`id`),
  CONSTRAINT `teacher_assignments_subjects_id_fk` FOREIGN KEY (`subject_id`) REFERENCES `input_subjects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `teacher_assignments_teachers_id_fk` FOREIGN KEY (`teacher_id`) REFERENCES `input_teachers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1551 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_teacher_days_off`
--

DROP TABLE IF EXISTS `input_teacher_days_off`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_teacher_days_off` (
  `id` int NOT NULL AUTO_INCREMENT,
  `teacher_id` int DEFAULT NULL,
  `day_of_week_id` int DEFAULT NULL,
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `input_teacher_days_off_pk` (`teacher_id`,`day_of_week_id`,`version_id`),
  KEY `teacher_days_off_days_of_week_id_fk` (`day_of_week_id`),
  KEY `fk_teacher_days_off_version` (`version_id`),
  CONSTRAINT `fk_teacher_days_off_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `teacher_days_off_days_of_week_id_fk` FOREIGN KEY (`day_of_week_id`) REFERENCES `input_days_of_week` (`id`),
  CONSTRAINT `teacher_days_off_teachers_id_fk` FOREIGN KEY (`teacher_id`) REFERENCES `input_teachers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_teacher_forbidden_slots`
--

DROP TABLE IF EXISTS `input_teacher_forbidden_slots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_teacher_forbidden_slots` (
  `id` int NOT NULL AUTO_INCREMENT,
  `teacher_id` int DEFAULT NULL,
  `day_of_week_id` int DEFAULT NULL,
  `slot_id` int DEFAULT NULL,
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `input_teacher_forbidden_slots_pk` (`teacher_id`,`day_of_week_id`,`slot_id`,`version_id`),
  KEY `teacher_forbidden_slots_days_of_week_id_fk` (`day_of_week_id`),
  KEY `fk_teacher_forbidden_slots_version` (`version_id`),
  CONSTRAINT `fk_teacher_forbidden_slots_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `teacher_forbidden_slots_days_of_week_id_fk` FOREIGN KEY (`day_of_week_id`) REFERENCES `input_days_of_week` (`id`),
  CONSTRAINT `teacher_forbidden_slots_teachers_id_fk` FOREIGN KEY (`teacher_id`) REFERENCES `input_teachers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_teacher_slot_weight`
--

DROP TABLE IF EXISTS `input_teacher_slot_weight`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_teacher_slot_weight` (
  `id` int NOT NULL AUTO_INCREMENT,
  `teacher_id` int DEFAULT NULL,
  `day_of_week_id` int DEFAULT NULL,
  `slot_id` int DEFAULT NULL,
  `weight` double DEFAULT NULL,
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `input_teacher_slot_weight_pk` (`teacher_id`,`day_of_week_id`,`slot_id`,`version_id`),
  KEY `teacher_slot_weight_days_of_week_id_fk` (`day_of_week_id`),
  KEY `fk_teacher_slot_weight_version` (`version_id`),
  CONSTRAINT `fk_teacher_slot_weight_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `teacher_slot_weight_days_of_week_id_fk` FOREIGN KEY (`day_of_week_id`) REFERENCES `input_days_of_week` (`id`),
  CONSTRAINT `teacher_slot_weight_teachers_id_fk` FOREIGN KEY (`teacher_id`) REFERENCES `input_teachers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_teachers`
--

DROP TABLE IF EXISTS `input_teachers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_teachers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `subject_group_id` int DEFAULT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `name_eng` varchar(100) NOT NULL DEFAULT (concat(_utf8mb4'teach',to_base64(random_bytes(5)))),
  `version_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `teachers_name_eng` (`name_eng`,`version_id`),
  KEY `fk_teachers_version` (`version_id`),
  CONSTRAINT `fk_teachers_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `input_time_slots`
--

DROP TABLE IF EXISTS `input_time_slots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `input_time_slots` (
  `period` int NOT NULL,
  `version_id` int DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `input_time_slots_pk` (`period`,`version_id`),
  KEY `fk_time_slots_version` (`version_id`),
  CONSTRAINT `fk_time_slots_version` FOREIGN KEY (`version_id`) REFERENCES `core_versions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'school_sheduller'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-10-05  3:50:09

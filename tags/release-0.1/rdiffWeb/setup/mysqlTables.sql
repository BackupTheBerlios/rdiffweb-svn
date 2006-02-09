drop database if exists rdiff_web;

create database rdiff_web;
use rdiff_web;

create table users ( UserID int(11) NOT NULL auto_increment,
FirstName varchar(50) not null,
LastName varchar(50) not null,
Username varchar(50) not null,
Password varchar(40) not null,
UserRoot varchar (255) not null,
UserEmail varchar (255) not null,
IsAdmin boolean not null,
primary key (UserID) );

create table repos ( UserID int(11) NOT NULL, RepoPath varchar (1024) not null);

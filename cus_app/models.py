"""
**models.py**: Defines the SQLAlchemy models for working with the Usint Database.

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Apr 28, 2025

:NOTE:In regular SQLAlchemy, the sqlalchemy.orm.DeclarativeBase parent class should be used to define the translation between Python classes that
represent an SQLAlchemy ORM structure system and relational database model statements.
For Flask SQLAlchemy, we use the instantiated db.Model as our parent class instead because it performs the same translations
while also tying the created ORM into the Flask application context.
In **__init__.py**, the db = SQLAlchemy() call will define the db.Model class with the sqlalchemy.orm.DeclarativeBase as a parent on our behalf.

:NOTE: Relationship declarations exist on the SQLAlchemy interface level and are not a part of the native SQLite table schema. They exist to provide an
object oriented relational mapping to related table entires.

:NOTE: The Usint database interface is supported by a set of interworking interfaces which require an understanding of PRG design approaches.
    This ensures that database writes are formatted successfully and not repeated upon new or refreshed requests.
        - PRG: https://en.wikipedia.org/wiki/Post/Redirect/Get
        - ACA Team Sybase Interface: https://github.com/sot/ska_dbi/blob/master/ska_dbi/sqsh.py
    
    The SQLite database interface libraries share a single "database" session per web request so that all users operate with the same data.
    This differs from a "web" session which stores data for the user in between web requests where common usage means they submit multiple web requests in a single sitting.

    Flask-Session commits to the usint database following every edit of the server-side cookie, which will also commit any pending transaction in the 
    SQLAlchemy database interface used for recording ocat revision information. This has the benefit of ensuring all web application processes are cleanly
    applied on the user side, at the expense of requiring careful monitoring of development work to ensure SQLAlchemy transactions and Flask-Session cookie updates
    occur separately during processing.
        - https://flask-session.readthedocs.io/en/latest/
        - https://flask-sqlalchemy.readthedocs.io/en/stable/
        - https://flask.palletsprojects.com/en/stable/api/#flask.session

"""
from flask_login import UserMixin
from .extensions import db
from typing import Optional, List #: Allows for Mapper to determine nullability of the table column.
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(db.Model, UserMixin):
    """
    SQLAlchemy ORM for the Usint users table. Serves as parent table for most other purposes.

    :id: Primary Key
    :username: HEAD POGO LDAP account username
    :is_active: Boolean listing if the user is still an active Usint personnel member
    :email: Email Address
    :groups: colon separated string listing group membership
    :full_name: First and last name
    """
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[int]= mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True)
    is_active: Mapped[bool] = mapped_column(nullable=False)
    email: Mapped[Optional[str]]
    groups: Mapped[Optional[str]]
    full_name: Mapped[Optional[str]]
    
    revisions: Mapped[List["Revision"]] = relationship(back_populates='user', foreign_keys="Revision.user_id")
    gen: Mapped[List["Signoff"]] = relationship(back_populates='general_signoff', foreign_keys="Signoff.general_signoff_id")
    acis: Mapped[List["Signoff"]] = relationship(back_populates='acis_signoff', foreign_keys="Signoff.acis_signoff_id")
    acis_si: Mapped[List["Signoff"]] = relationship(back_populates='acis_si_signoff', foreign_keys="Signoff.acis_si_signoff_id")
    hrc_si: Mapped[List["Signoff"]] = relationship(back_populates='hrc_si_signoff', foreign_keys="Signoff.hrc_si_signoff_id")
    usint: Mapped[List["Signoff"]] = relationship(back_populates='usint_signoff', foreign_keys="Signoff.usint_signoff_id")
    schedules: Mapped[List["Schedule"]] = relationship(back_populates='user', foreign_keys="Schedule.user_id")

    def to_dict(self):
        """Maps table columns to value as a python dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self) -> str:
         return f"User(id={self.id!r}, username={self.username!r}, email={self.email!r}, groups={self.groups!r}, full_name={self.full_name!r})"

class Revision(db.Model):
    """
    SQLAlchemy ORM for an observation revision. Serves as parent table for Signoffs and parameter state tables Originals and Requests

    :id: Primary Key
    :obsid: Observation ID
    :revision_number: Identifying count of revisions for this obsid (indexing at one)
    :kind: Type of revision (norm, asis, remove, clone)
        - norm: Parameter value change
        - asis: Observation setup is approved as is
        - remove: Mark the observation as removed from the approved list
        - clone: Request the observation be split into multiple obsids.
    :sequence_number: Sequence Number
    :time: Epoch timestamp of when revision was created.
    :notes: JSON formatted notes of revision specifics (usually a special norm change)
    If not present assume false.
        - target_name_change : Booelan
        - comment_change : Boolean
        - instrument_change : Boolean
        - grating_change : Boolean
        - flag_change : Boolean, listed for any change in constraint-specific parameters (dither, time, roll, ACIS window)
        - large_coordinate_change : Boolean, listed for a >8' cumulative shift in RA, DEC coordinates
        - obsdate_under10: Boolean, listed if the soe_st_sched_date or lts_lt_plan dates are within 10 days of the revision
        - on_or_list: Boolean, listed if obsid in the revision is in on the active OR list
    :user_id: Foreign Key to matching User submitting the revision to
    
    """
    __tablename__ = "revisions"
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    obsid: Mapped[int] = mapped_column(nullable=False)
    revision_number: Mapped[int] = mapped_column(nullable=False)
    kind: Mapped[str] = mapped_column(nullable=False)
    sequence_number: Mapped[int] = mapped_column(nullable=False)
    time: Mapped[int] = mapped_column(nullable=False)
    notes: Mapped[str] = mapped_column(nullable=True)
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable = False)
        
    user: Mapped["User"] = relationship(back_populates='revisions', foreign_keys=user_id)
    signoff: Mapped["Signoff"] = relationship(back_populates='revision', foreign_keys="Signoff.revision_id", uselist=False, cascade="all, delete", passive_deletes=True)
        
    request: Mapped[List["Request"]] = relationship(back_populates='revision', foreign_keys="Request.revision_id", cascade="all, delete, delete-orphan", passive_deletes=True)
    original: Mapped[List["Original"]] = relationship(back_populates='revision', foreign_keys="Original.revision_id", cascade="all, delete, delete-orphan", passive_deletes=True)
        
    def to_dict(self):
        """Maps table columns to value as a python dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def obsidrev(self):
        """String representation of the obsid.rev key"""
        return f"{self.obsid}.{self.revision_number:>03}"

    def __repr__(self) -> str:
        return f"Revision(id={self.id!r}, user_id={self.user_id!r}, obsid={self.obsid!r}, revision_number={self.revision_number!r}, kind={self.kind!r})"

class Signoff(db.Model):
    """
    Signoff Table ORM. The possible status options are ('Signed', 'Not Required', 'Pending', 'Discard')

    :id: Primary Key
    :revision_id: Foreign Key to matching Revision table entry Primary Key
    
    :general_status: String determining the status of the general signoff column
    :general_signoff_id: Integer matching the user who performed the general signoff. Can be Null if signoff not necessary.
    :general_time: Epoch timestamp of when the general signoff was made. Can be Null if signoff not necessary.

    :acis_status: String determining the status of the acis signoff column
    :acis_signoff_id: Integer matching the user who performed the acis signoff. Can be Null if signoff not necessary.
    :acis_time: Epoch timestamp of when the acis signoff was made. Can be Null if signoff not necessary.

    :acis_si_status: String determining the status of the acis_si signoff column
    :acis_si_signoff_id: Integer matching the user who performed the acis_si signoff. Can be Null if signoff not necessary.
    :acis_si_time: Epoch timestamp of when the acis_si signoff was made. Can be Null if signoff not necessary.

    :hrc_si_status: String determining the status of the hrc_si signoff column
    :hrc_si_signoff_id: Integer matching the user who performed the hrc_si signoff. Can be Null if signoff not necessary.
    :hrc_si_time: Epoch timestamp of when the hrc_si signoff was made. Can be Null if signoff not necessary.

    :usint_status: String determining the status of the usint signoff column
    :usint_signoff_id: Integer matching the user who performed the usint signoff. Can be Null if signoff not necessary.
    :usint_time: Epoch timestamp of when the usint signoff was made. Can be Null if signoff not necessary.
    """
    __tablename__ = "signoffs"
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    revision_id: Mapped[int] = mapped_column(ForeignKey("revisions.id", ondelete="CASCADE"), nullable=False, unique=True)
    revision: Mapped["Revision"] = relationship(back_populates='signoff', foreign_keys=revision_id, single_parent=True)
        
    general_status: Mapped[str] = mapped_column(nullable = False)
    general_signoff_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable = True)
    general_signoff: Mapped[Optional["User"]] = relationship(back_populates='gen', foreign_keys=general_signoff_id)
    general_time: Mapped[Optional[int]]
        
    acis_status: Mapped[str] = mapped_column(nullable = False)
    acis_signoff_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable = True)
    acis_signoff: Mapped[Optional["User"]] = relationship(back_populates='acis', foreign_keys=acis_signoff_id)
    acis_time: Mapped[Optional[int]]
        
    acis_si_status: Mapped[str] = mapped_column(nullable = False)
    acis_si_signoff_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable = True)
    acis_si_signoff: Mapped[Optional["User"]] = relationship(back_populates='acis_si', foreign_keys=acis_si_signoff_id)
    acis_si_time: Mapped[Optional[int]]
    
    hrc_si_status: Mapped[str] = mapped_column(nullable = False)
    hrc_si_signoff_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable = True)
    hrc_si_signoff: Mapped[Optional["User"]] = relationship(back_populates='hrc_si', foreign_keys=hrc_si_signoff_id)
    hrc_si_time: Mapped[Optional[int]]
    
    usint_status: Mapped[str] = mapped_column(nullable = False)
    usint_signoff_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable = True)
    usint_signoff: Mapped[Optional["User"]] = relationship(back_populates='usint', foreign_keys=usint_signoff_id)
    usint_time: Mapped[Optional[int]]
    
    def to_dict(self):
        """Maps table columns to value as a python dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self) -> str:
        return f"Signoff(id={self.id!r}, revision={self.revision!r}, usint_signoff_id={self.usint_signoff_id!r})"

class Parameter(db.Model):
    """
    Observation parameters as listed in the OCAT

    :id: Primary key
    :name: Parameter name as listed in the OCAT.
    :is_modifiable: Boolean marking if the listed parameter can be changed by Usint users.
    :data_type: String description of the parameter datatype
    :description: Paragraph detailing information about the parameter.
    """
    __tablename__ = 'parameters'
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
    request: Mapped[List["Request"]] = relationship(back_populates='parameter', foreign_keys="Request.parameter_id")
    original: Mapped[List["Original"]] = relationship(back_populates='parameter', foreign_keys="Original.parameter_id")
        
    name: Mapped[str] = mapped_column(unique=True, nullable= False)
    is_modifiable : Mapped[bool] = mapped_column(nullable = False)
    data_type: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    
    def to_dict(self):
        """Maps table columns to value as a python dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self) -> str:
        return f"Parameter(id={self.id!r}, name={self.name!r}, data_type={self.data_type!r})"

class Request(db.Model):
    """
    Table for the set or parameter change requests paired with a revision.

    :id: Primary key
    :revision_id: Foreign Key to matching Revision table entry Primary Key
    :parameter_id: Foreign Key to matching Parameter table entry Primary Key
    :value: JSON formatted string of the requested value change. Can be NULL, which means it's requested to be nullified.
    """
    __tablename__ = 'requests'
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
    revision_id: Mapped[int] = mapped_column(ForeignKey("revisions.id", ondelete="CASCADE"), nullable=False)
    revision: Mapped["Revision"] = relationship(back_populates="request", foreign_keys=revision_id)
        
    parameter_id: Mapped[int] = mapped_column(ForeignKey("parameters.id"))
    parameter: Mapped["Parameter"] = relationship(back_populates="request", foreign_keys=parameter_id)
    
    value: Mapped[str] = mapped_column(nullable=True)

    def to_dict(self):
        """Maps table columns to value as a python dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self) -> str:
        return f"Request(id={self.id!r}, revision_id={self.revision_id!r}, parameter_id={self.parameter_id!r}, value={self.value!r})"

class Original(db.Model):
    """
    Table for the set of original parameter values paired with a revision.

    :id: Primary key
    :revision_id: Foreign Key to matching Revision table entry Primary Key
    :parameter_id: Foreign Key to matching Parameter table entry Primary Key
    :value: JSON formatted string of original values. If an observation parameter is not listed for an obsid.rev, assume it's NULL.
    """
    __tablename__ = 'originals'
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
    revision_id: Mapped[int] = mapped_column(ForeignKey("revisions.id", ondelete="CASCADE"), nullable=False)
    revision: Mapped["Revision"] = relationship(back_populates="original", foreign_keys=revision_id)
    
    parameter_id: Mapped[int] = mapped_column(ForeignKey("parameters.id"))
    parameter: Mapped["Parameter"] = relationship(back_populates="original", foreign_keys=parameter_id)
    #
    #--- By convention, we don't want to store null values in the original state representation of the obsid parameters.
    #--- This can be inferred by the lack of this parameter in the table for a specific revision.
    #--- For example, an obsid could have no y_det_offset both before and after a specific norm revision, so we don't record that information.
    #--- Nevertheless, the value column can take NULL values to future-proof edge cases.
    #
    value: Mapped[str] = mapped_column(nullable=True)
    
    def to_dict(self):
        """Maps table columns to value as a python dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self) -> str:
        return f"Original(order_id={self.order_id!r}, revision_id={self.revision_id!r}, parameter_id={self.parameter_id!r}, value={self.value!r})"

class Schedule(db.Model):
    """
    Table for recording TOO POC duty scheduled time periods.

    :NOTE: By convention, a time period should not exceed a week of assigned duty (marked as six days since it's understood that the stop occurs at the end of the day)

    
    :id: Primary Key
    :order_id: Secondary pseudo-primary key to determine intended order of schedule entires, rather than their creation order demonstrated by the primary key
    :user_id: User ID for POC on duty for that time period
    :start: Datetime of the start of POC duty (start of provided date)
    :stop: Datetime of the end of POC duty (end of provided date)
    :assigner_id: User ID of the user who assigned this time period's POC duty
    """
    __tablename__ = 'schedules'
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
    #
    # --- order_id acts as changeable identification of the schedule order for easy fetching of adjacent time period entires
    #
    order_id: Mapped[int] = mapped_column(nullable = True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable = True)
    user: Mapped["User"] = relationship(back_populates='schedules', foreign_keys=user_id)
    start: Mapped[datetime] = mapped_column(nullable = False)
    stop: Mapped[datetime] = mapped_column(nullable = False)
    #: Note that the assigner_id is not treated as other Foreign Key relationships as its usage is always the current user in the application.
    assigner_id: Mapped[int] = mapped_column(nullable = True)
    
    def to_dict(self):
        """Maps table columns to value as a python dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def __repr__(self) -> str:
        return f"Schedule(order_id={self.order_id!r}, user_id={self.user_id!r}, start={self.start!r}, stop={self.stop!r})"
from datetime import *
from decimal import *
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

% for table in tables:
class ${table['class_name']}(Base):
    __tablename__ = '${table['name']}'

    % for column in table['columns']:
    % if column['foreign_key']:
    ${column['name']}: Mapped[${column['type']}] = mapped_column(
        ${column['foreign_key']}
        ${column['args']}
    )
    % else:
    ${column['name']}: Mapped[${column['type']}] = mapped_column(${column['args']})\
    % endif

    % endfor



% endfor
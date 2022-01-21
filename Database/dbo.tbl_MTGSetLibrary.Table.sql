/****** Object:  Table [dbo].[tbl_MTGSetLibrary]    Script Date: 1/21/2022 8:27:24 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[tbl_MTGSetLibrary](
	[setPK] [int] IDENTITY(1,1) NOT NULL,
	[setName] [varchar](200) NULL,
	[setCode] [varchar](5) NULL,
 CONSTRAINT [PK_tbl_MTGSetLibrary] PRIMARY KEY CLUSTERED 
(
	[setPK] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO

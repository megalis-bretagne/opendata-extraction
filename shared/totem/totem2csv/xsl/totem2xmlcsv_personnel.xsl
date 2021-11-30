<?xml version="1.0" encoding="UTF-8"?>
<!--
Transform TOTEM xml Annexe Personnel file into CSV like XML file

TOTEM: http://odm-budgetaire.org/

author: Vincent Kober, Données et Cie Grenoble
-->
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:totem="http://www.minefi.gouv.fr/cp/demat/docbudgetaire">
  <xsl:output method="xml" encoding="utf-8" />

    <xsl:template match="/">
        <xsl:variable name="NatDec" select="//totem:BlocBudget/totem:NatDec/@V" />
        <xsl:variable name="Exer" select="//totem:BlocBudget/totem:Exer/@V" />
        <xsl:variable name="IdEtab" select="//totem:EnTeteBudget/totem:IdEtab/@V" />
        <xsl:variable name="LibelleColl" select="//totem:EnTeteDocBudgetaire/totem:LibelleColl/@V" />
        <csv>
            <header>
                <column name="BGT_NATDEC"/>
                <column name="BGT_ANNEE"/>
                <column name="BGT_SIRET"/>
                <column name="BGT_NOM"/>
                <column name="BGT_CODTYPAGENT"/>
                <column name="BGT_EMPLOIGRADEAGENT"/>
                <column name="BGT_CODCATAGENT"/>
                <column name="BGT_TEMPSCOMPLET"/>
                <column name="BGT_PERMANENT"/>
                <column name="BGT_NATURECONTRAT"/>
                <column name="BGT_LIBELLENATURECONTRAT"/>
                <column name="BGT_CODESECTAGENTTITULAIRE"/>
                <column name="BGT_REMUNAGENT"/>
                <column name="BGT_MTPREV6215"/>
                <column name="BGT_INDICEAGENT"/>
                <column name="BGT_CODMOTIFCONTRATAGENT"/>
                <column name="BGT_LIBMOTIFCONTRATAGENT"/>
                <column name="BGT_EFFECTIFBUD"/>
                <column name="BGT_EFFECTIFPOURVU"/>
                <column name="BGT_EFFECTIFTNC"/>
                <column name="BGT_CHAMP_EDITEUR"/>
            </header>
            <data>
                <xsl:for-each select=".//totem:PERSONNEL">
                    <row lineno="{position()}">
                        <cell name="BGT_NATDEC" value="{$NatDec}" />
                        <cell name="BGT_ANNEE" value="{$Exer}" />
                        <cell name="BGT_SIRET" value="{$IdEtab}" />
                        <cell name="BGT_NOM" value="{$LibelleColl}" />
                        <xsl:if test="totem:CodTypAgent">
                          <cell name="BGT_CODTYPAGENT" value="{totem:CodTypAgent/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:EmploiGradeAgent">
                          <cell name="BGT_EMPLOIGRADEAGENT" value="{totem:EmploiGradeAgent/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:CodCatAgent">
                          <cell name="BGT_CODCATAGENT" value="{totem:CodCatAgent/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:TempsComplet">
                          <cell name="BGT_TEMPSCOMPLET" value="{totem:TempsComplet/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:Permanent">
                          <cell name="BGT_PERMANENT" value="{totem:Permanent/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:NatureContrat">
                          <cell name="BGT_NATURECONTRAT" value="{totem:NatureContrat/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:LibelleNatureContrat">
                          <cell name="BGT_LIBELLENATURECONTRAT" value="{totem:LibelleNatureContrat/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:CodSectAgentTitulaire">
                          <cell name="BGT_CODESECTAGENTTITULAIRE" value="{totem:CodSectAgentTitulaire/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:RemunAgent">
                          <cell name="BGT_REMUNAGENT" value="{totem:RemunAgent/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtPrev6215">
                          <cell name="BGT_MTPREV6215" value="{totem:MtPrev6215/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:IndiceAgent">
                          <cell name="BGT_INDICEAGENT" value="{totem:IndiceAgent/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:CodMotifContrAgent">
                          <cell name="BGT_CODMOTIFCONTRATAGENT" value="{totem:CodMotifContrAgent/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:LibMotifContrAgent">
                          <cell name="BGT_LIBMOTIFCONTRATAGENT" value="{totem:LibMotifContrAgent/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:EffectifBud">
                          <cell name="BGT_EFFECTIFBUD" value="{totem:EffectifBud/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:EffectifPourvu">
                          <cell name="BGT_EFFECTIFPOURVU" value="{totem:EffectifPourvu/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:EffectifTNC">
                          <cell name="BGT_EFFECTIFTNC" value="{totem:EffectifTNC/@V}"/>
                        </xsl:if>
                        <xsl:if test="totem:Champ_Editeur">
                          <cell name="BGT_CHAMP_EDITEUR" value="{totem:Champ_Editeur/@V}" />
                        </xsl:if>
                    </row>
                </xsl:for-each>
            </data>
        </csv>
    </xsl:template>

    <xsl:template match="totem:PERSONNEL">
        <xsl:copy-of select="."/>
    </xsl:template>

</xsl:stylesheet>
